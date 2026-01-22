"""
セキュリティモジュール
JWT生成・検証、パスワードハッシュ化
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import os

# パスワードハッシュ化
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT設定
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))


def hash_password(password: str) -> str:
    """
    パスワードをハッシュ化
    
    Args:
        password: 平文パスワード
    
    Returns:
        bcryptハッシュ
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    パスワード検証
    
    Args:
        plain_password: 平文パスワード
        hashed_password: ハッシュ化パスワード
    
    Returns:
        検証結果
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    アクセストークン生成
    
    Args:
        data: トークンに含めるデータ（user_id, email等）
        expires_delta: 有効期限（オプション）
    
    Returns:
        JWT文字列
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    リフレッシュトークン生成
    
    Args:
        data: トークンに含めるデータ
    
    Returns:
        JWT文字列
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    トークン検証
    
    Args:
        token: JWT文字列
        token_type: トークンタイプ（access/refresh）
    
    Returns:
        デコードされたペイロード、無効な場合はNone
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # トークンタイプ確認
        if payload.get("type") != token_type:
            return None
        
        return payload
    
    except JWTError:
        return None


def generate_password_reset_token() -> str:
    """
    パスワードリセットトークン生成（ランダム文字列）
    
    Returns:
        32文字のランダムトークン
    """
    return secrets.token_urlsafe(32)


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    パスワード強度検証
    
    Args:
        password: 検証するパスワード
    
    Returns:
        (有効か, エラーメッセージ)
    """
    min_length = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters"
    
    # 将来的に他の検証を追加可能
    # require_uppercase, require_digit等
    
    return True, None