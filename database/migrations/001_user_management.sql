-- =====================================
-- User Management Migration
-- Phase 1: MVP
-- =====================================

-- 1. users テーブル
CREATE TABLE IF NOT EXISTS public.users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_active ON public.users(is_active) WHERE is_active = true;

-- 2. roles テーブル
CREATE TABLE IF NOT EXISTS public.roles (
    role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    description TEXT,
    is_system_role BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO public.roles (role_name, display_name, description, is_system_role) VALUES
    ('user', '一般ユーザー', '基本的な機能を利用できるユーザー', true),
    ('admin', '管理者', 'システム全体を管理できるユーザー', true)
ON CONFLICT (role_name) DO NOTHING;

-- 3. user_roles テーブル
CREATE TABLE IF NOT EXISTS public.user_roles (
    user_role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES public.roles(role_id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, role_id)
);

CREATE INDEX idx_user_roles_user ON public.user_roles(user_id);
CREATE INDEX idx_user_roles_role ON public.user_roles(role_id);

-- 4. user_domain_access テーブル
CREATE TABLE IF NOT EXISTS public.user_domain_access (
    access_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    domain_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by UUID REFERENCES public.users(user_id),
    reason TEXT,
    notes TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, domain_id)
);

CREATE INDEX idx_user_domain_access_user ON public.user_domain_access(user_id);
CREATE INDEX idx_user_domain_access_domain ON public.user_domain_access(domain_id);
CREATE INDEX idx_user_domain_access_status ON public.user_domain_access(status);

-- 5. conversations テーブル
CREATE TABLE IF NOT EXISTS public.conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    domain VARCHAR(50) NOT NULL,
    title VARCHAR(500),
    is_pinned BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_user ON public.conversations(user_id);
CREATE INDEX idx_conversations_domain ON public.conversations(domain);
CREATE INDEX idx_conversations_updated ON public.conversations(updated_at DESC);
CREATE INDEX idx_conversations_user_domain ON public.conversations(user_id, domain);

-- 6. messages テーブル
CREATE TABLE IF NOT EXISTS public.messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(conversation_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_conversation ON public.messages(conversation_id);
CREATE INDEX idx_messages_created ON public.messages(created_at);

-- 7. refresh_tokens テーブル
CREATE TABLE IF NOT EXISTS public.refresh_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT false,
    revoked_at TIMESTAMP,
    user_agent TEXT,
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_refresh_tokens_token ON public.refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_user ON public.refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires ON public.refresh_tokens(expires_at);

-- 8. password_reset_tokens テーブル
CREATE TABLE IF NOT EXISTS public.password_reset_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT false,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_password_reset_tokens_token ON public.password_reset_tokens(token);
CREATE INDEX idx_password_reset_tokens_user ON public.password_reset_tokens(user_id);

-- 9. audit_logs テーブル
CREATE TABLE IF NOT EXISTS public.audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(user_id),
    action VARCHAR(100) NOT NULL,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_date ON public.audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_action ON public.audit_logs(action, created_at DESC);

-- Row Level Security
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY conversations_user_isolation ON public.conversations
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', true)::uuid);

CREATE POLICY conversations_admin_access ON public.conversations
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.role_id
            WHERE ur.user_id = current_setting('app.current_user_id', true)::uuid
              AND r.role_name = 'admin'
        )
    );

CREATE POLICY messages_user_isolation ON public.messages
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.conversations c
            WHERE c.conversation_id = messages.conversation_id
              AND c.user_id = current_setting('app.current_user_id', true)::uuid
        )
    );

-- Triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON public.conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_domain_access_updated_at
    BEFORE UPDATE ON public.user_domain_access
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 初期データ: デフォルト管理者
-- パスワード: admin123（本番では必ず変更）
DO $$
DECLARE
    v_user_id UUID;
    v_role_id UUID;
BEGIN
    -- ユーザー作成
    INSERT INTO public.users (email, password_hash, display_name, is_active, is_verified)
    VALUES (
        'admin@example.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7gO.5cBYSq',
        'Administrator',
        true,
        true
    )
    ON CONFLICT (email) DO NOTHING
    RETURNING user_id INTO v_user_id;
    
    -- ロール付与
    IF v_user_id IS NOT NULL THEN
        SELECT role_id INTO v_role_id FROM public.roles WHERE role_name = 'admin';
        
        INSERT INTO public.user_roles (user_id, role_id)
        VALUES (v_user_id, v_role_id)
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

-- 確認
SELECT 'User Management Migration Complete' AS status;