"""
認証API
"""
from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import Optional

from app.auth.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    LoginResponse
)
from app.auth.service import auth_service  # ← インスタンスをインポート
from app.auth.dependencies import get_current_user, get_current_active_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserRegisterRequest):
    """
    ユーザー登録
    
    Args:
        request: 登録データ
    
    Returns:
        ユーザー情報
    
    Raises:
        HTTPException: 登録失敗
    """
    try:
        user_info = auth_service.register_user(request)  # ← auth_service.を使用
        return user_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=LoginResponse)
async def login(request: UserLoginRequest, http_request: Request):
    """
    ログイン
    
    Args:
        request: ログインデータ
        http_request: HTTPリクエスト
    
    Returns:
        ログイン情報（ユーザー、トークン）
    
    Raises:
        HTTPException: ログイン失敗
    """
    try:
        # IPアドレスとUser-Agent取得
        ip_address = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")
        
        login_info = auth_service.login_user(  # ← auth_service.を使用
            request,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return login_info
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_active_user),
    refresh_token: Optional[str] = None
):
    """
    ログアウト
    
    Args:
        current_user: 現在のユーザー
        refresh_token: リフレッシュトークン（オプション）
    
    Returns:
        成功メッセージ
    """
    try:
        auth_service.logout_user(  # ← auth_service.を使用
            user_id=current_user["user_id"],
            refresh_token=refresh_token
        )
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_active_user)):
    """
    現在のユーザー情報取得
    
    Args:
        current_user: 現在のユーザー
    
    Returns:
        ユーザー情報
    """
    return current_user


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """
    トークンリフレッシュ（Phase 2実装予定）
    
    Args:
        refresh_token: リフレッシュトークン
    
    Returns:
        新しいアクセストークン
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not implemented yet (Phase 2)"
    )


@router.post("/password-reset-request")
async def password_reset_request(email: str):
    """
    パスワードリセット要求（Phase 2実装予定）
    
    Args:
        email: メールアドレス
    
    Returns:
        成功メッセージ
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not implemented yet (Phase 2)"
    )


@router.post("/password-reset-confirm")
async def password_reset_confirm(token: str, new_password: str):
    """
    パスワードリセット確認（Phase 2実装予定）
    
    Args:
        token: リセットトークン
        new_password: 新しいパスワード
    
    Returns:
        成功メッセージ
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset confirmation not implemented yet (Phase 2)"
    )


@router.post("/password-change")
async def password_change(
    current_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    パスワード変更（Phase 2実装予定）
    
    Args:
        current_password: 現在のパスワード
        new_password: 新しいパスワード
        current_user: 現在のユーザー
    
    Returns:
        成功メッセージ
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password change not implemented yet (Phase 2)"
    )