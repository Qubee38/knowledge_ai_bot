"""
認証関連のPydanticスキーマ
リクエスト/レスポンスモデル
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
import uuid


# ========================================
# リクエストスキーマ
# ========================================

class UserRegisterRequest(BaseModel):
    """ユーザー登録リクエスト"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: Optional[str] = Field(None, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        """パスワード検証"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class UserLoginRequest(BaseModel):
    """ログインリクエスト"""
    email: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    """トークンリフレッシュリクエスト"""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """パスワードリセット要求"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """パスワードリセット確認"""
    token: str
    new_password: str = Field(..., min_length=8)


class PasswordChange(BaseModel):
    """パスワード変更"""
    current_password: str
    new_password: str = Field(..., min_length=8)


# ========================================
# レスポンススキーマ
# ========================================

class UserResponse(BaseModel):
    """ユーザー情報レスポンス"""
    user_id: uuid.UUID
    email: str
    display_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """トークンレスポンス"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒数


class LoginResponse(BaseModel):
    """ログインレスポンス"""
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RoleResponse(BaseModel):
    """ロール情報"""
    role_id: uuid.UUID
    role_name: str
    display_name: Optional[str]
    
    class Config:
        from_attributes = True


class UserWithRolesResponse(BaseModel):
    """ロール情報付きユーザー"""
    user: UserResponse
    roles: List[RoleResponse]


# ========================================
# ドメインアクセス関連
# ========================================

class DomainAccessRequest(BaseModel):
    """ドメインアクセス申請"""
    reason: Optional[str] = Field(None, max_length=500)


class DomainAccessResponse(BaseModel):
    """ドメインアクセスレスポンス"""
    access_id: uuid.UUID
    domain_id: str
    status: str
    requested_at: datetime
    approved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class DomainInfo(BaseModel):
    """ドメイン情報"""
    domain_id: str
    name: str
    description: str
    access_status: Optional[str]  # 'active', 'pending', None（未申請）
    requested_at: Optional[datetime]
    approved_at: Optional[datetime]