#!/bin/bash
# ユーザー管理マイグレーション実行スクリプト

set -e

echo "================================"
echo "User Management Migration"
echo "================================"

# PostgreSQLコンテナ名
POSTGRES_CONTAINER="postgres"

# データベース名
DATABASE_NAME="knowledge_ai_bot"

# マイグレーションファイル
MIGRATION_FILE="/docker-entrypoint-initdb.d/migrations/001_user_management.sql"

echo ""
echo "Step 1: PostgreSQLコンテナ確認..."
docker-compose ps | grep postgres

echo ""
echo "Step 2: マイグレーション実行..."
docker-compose exec -T $POSTGRES_CONTAINER psql -U postgres -d $DATABASE_NAME -f $MIGRATION_FILE

echo ""
echo "Step 3: テーブル確認..."
docker-compose exec -T $POSTGRES_CONTAINER psql -U postgres -d $DATABASE_NAME -c "
SELECT 
    schemaname as schema,
    tablename as table
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
"

echo ""
echo "Step 4: デフォルト管理者確認..."
docker-compose exec -T $POSTGRES_CONTAINER psql -U postgres -d $DATABASE_NAME -c "
SELECT email, display_name, is_active 
FROM public.users 
WHERE email = 'admin@example.com';
"

echo ""
echo "✅ Migration completed successfully!"
echo ""
echo "デフォルト管理者アカウント:"
echo "  Email: admin@example.com"
echo "  Password: admin123"
echo "  ⚠️ 本番環境では必ずパスワードを変更してください"
echo ""