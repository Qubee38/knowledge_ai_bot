"""
認証依存性注入
FastAPIのDependsで使用する認証関数
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import uuid
import logging

from app.core.security import verify_token
from app.auth.service import auth_service

logger = logging.getLogger(__name__)

# HTTPベアラー認証スキーム
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    現在のユーザー取得（JWT検証）
    
    Args:
        credentials: HTTPベアラートークン
    
    Returns:
        ユーザー情報辞書
    
    Raises:
        HTTPException: 認証失敗時
    """
    token = credentials.credentials
    
    # トークン検証
    payload = verify_token(token, token_type="access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # ユーザーID取得
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # ユーザー情報取得
    user = auth_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # アクティブチェック
    if not user.get('is_active', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    アクティブユーザー取得
    
    Args:
        current_user: 現在のユーザー
    
    Returns:
        アクティブユーザー情報
    
    Raises:
        HTTPException: ユーザーが非アクティブの場合
    """
    if not current_user.get('is_active', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return current_user


async def get_current_admin_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    管理者ユーザー取得
    
    Args:
        current_user: 現在のユーザー
    
    Returns:
        管理者ユーザー情報
    
    Raises:
        HTTPException: 管理者権限がない場合
    """
    user_id = uuid.UUID(current_user['user_id'])
    roles = auth_service.get_user_roles(user_id)
    
    if 'admin' not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


def optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    オプショナルな認証（認証なしでもアクセス可能）
    
    Args:
        credentials: HTTPベアラートークン（オプション）
    
    Returns:
        ユーザー情報（認証されている場合）、None（未認証の場合）
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_token(token, token_type="access")
        
        if not payload:
            return None
        
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        
        user_id = uuid.UUID(user_id_str)
        user = auth_service.get_user_by_id(user_id)
        
        return user
    
    except Exception as e:
        logger.warning(f"Optional auth failed: {e}")
        return None