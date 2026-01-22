"""
認証サービス
ユーザー登録、ログイン、認証処理
"""
import uuid
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    validate_password_strength
)
from app.core.db_utils import get_db_connection, close_db_connection
from app.auth.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    LoginResponse
)

logger = logging.getLogger(__name__)


class AuthService:
    """認証サービスクラス"""
    
    def register_user(self, data: UserRegisterRequest) -> Dict[str, Any]:
        """
        ユーザー登録
        
        Args:
            data: 登録データ
        
        Returns:
            ユーザー情報
        
        Raises:
            ValueError: バリデーションエラー
            Exception: 登録失敗
        """
        conn = None
        cursor = None
        
        try:
            # パスワード強度チェック
            if not validate_password_strength(data.password):
                raise ValueError("Password does not meet requirements (minimum 8 characters)")
            
            # パスワードハッシュ化
            password_hash = hash_password(data.password)
            
            # DB接続
            conn, cursor = get_db_connection()
            
            # メール重複チェック
            cursor.execute(
                "SELECT user_id FROM public.users WHERE email = %s",
                (data.email,)
            )
            if cursor.fetchone():
                raise ValueError("Email already registered")
            
            # ユーザー作成
            user_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO public.users (
                    user_id, email, password_hash, display_name, is_active, is_verified
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING user_id, email, display_name, is_active, is_verified, 
                          created_at, updated_at, last_login_at
            """, (
                user_id,
                data.email,
                password_hash,
                data.display_name,
                True,
                False
            ))
            
            user = cursor.fetchone()
            
            # デフォルトロール（user）を付与
            cursor.execute("""
                INSERT INTO public.user_roles (user_id, role_id)
                SELECT %s, role_id
                FROM public.roles
                WHERE role_name = 'user'
            """, (user_id,))
            
            conn.commit()
            
            # 監査ログ
            self._log_audit(
                user_id=user_id,
                action="user.register",
                details={"email": data.email}
            )
            
            logger.info(f"User registered successfully: {data.email}")
            
            return {
                "user_id": user["user_id"],
                "email": user["email"],
                "display_name": user["display_name"],
                "is_active": user["is_active"],
                "is_verified": user["is_verified"],
                "created_at": user["created_at"],
                "updated_at": user["updated_at"],
                "last_login_at": user["last_login_at"]
            }
            
        except ValueError as e:
            logger.error(f"Registration validation error: {e}")
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Registration error: {e}")
            raise Exception("Failed to register user")
        finally:
            close_db_connection(conn, cursor)
    
    def login_user(
        self,
        data: UserLoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ユーザーログイン
        
        Args:
            data: ログインデータ
            ip_address: IPアドレス
            user_agent: ユーザーエージェント
        
        Returns:
            ログイン情報（ユーザー、トークン）
        
        Raises:
            ValueError: 認証失敗
        """
        conn = None
        cursor = None
        
        try:
            # DB接続
            conn, cursor = get_db_connection()
            
            # ユーザー取得
            cursor.execute("""
                SELECT 
                    user_id, email, password_hash, display_name, 
                    is_active, is_verified, created_at, updated_at, last_login_at
                FROM public.users
                WHERE email = %s
            """, (data.email,))
            
            user = cursor.fetchone()
            
            if not user:
                raise ValueError("Invalid email or password")
            
            # パスワード検証
            if not verify_password(data.password, user["password_hash"]):
                raise ValueError("Invalid email or password")
            
            # アクティブチェック
            if not user["is_active"]:
                raise ValueError("Account is inactive")
            
            # トークン生成
            access_token = create_access_token({"sub": str(user["user_id"])})
            refresh_token = create_refresh_token({"sub": str(user["user_id"])})
            
            # 最終ログイン時刻更新
            cursor.execute("""
                UPDATE public.users
                SET last_login_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (str(user["user_id"]),))
            
            # リフレッシュトークン保存
            cursor.execute("""
                INSERT INTO public.refresh_tokens (user_id, token, expires_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP + INTERVAL '30 days')
            """, (str(user["user_id"]), refresh_token))
            
            conn.commit()
            
            # 監査ログ
            self._log_audit(
                user_id=str(user["user_id"]),
                action="user.login",
                details={
                    "email": data.email,
                    "ip_address": ip_address,
                    "user_agent": user_agent
                }
            )
            
            logger.info(f"User logged in: {data.email}")
            
            return {
                "user": {
                    "user_id": user["user_id"],
                    "email": user["email"],
                    "display_name": user["display_name"],
                    "is_active": user["is_active"],
                    "is_verified": user["is_verified"],
                    "created_at": user["created_at"],
                    "updated_at": user["updated_at"],
                    "last_login_at": user["last_login_at"]
                },
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 1800  # 30分
            }
            
        except ValueError as e:
            logger.error(f"Login validation error: {e}")
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Login error: {e}")
            raise Exception("Failed to login")
        finally:
            close_db_connection(conn, cursor)
    
    def logout_user(
        self,
        user_id: str,
        refresh_token: Optional[str] = None
    ) -> bool:
        """
        ユーザーログアウト
        
        Args:
            user_id: ユーザーID
            refresh_token: リフレッシュトークン
        
        Returns:
            成功フラグ
        """
        conn = None
        cursor = None
        
        try:
            conn, cursor = get_db_connection()
            
            # リフレッシュトークン無効化
            if refresh_token:
                cursor.execute("""
                    UPDATE public.refresh_tokens
                    SET revoked = TRUE
                    WHERE user_id = %s AND token = %s
                """, (user_id, refresh_token))
            else:
                # 全トークン無効化
                cursor.execute("""
                    UPDATE public.refresh_tokens
                    SET revoked = TRUE
                    WHERE user_id = %s
                """, (user_id,))
            
            conn.commit()
            
            # 監査ログ
            self._log_audit(
                user_id=user_id,
                action="user.logout",
                details={}
            )
            
            logger.info(f"User logged out: {user_id}")
            
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Logout error: {e}")
            return False
        finally:
            close_db_connection(conn, cursor)
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        ユーザーID指定でユーザー情報取得
        
        Args:
            user_id: ユーザーID
        
        Returns:
            ユーザー情報 or None
        """
        conn = None
        cursor = None
        
        try:
            conn, cursor = get_db_connection()
            
            cursor.execute("""
                SELECT 
                    user_id, email, display_name, 
                    is_active, is_verified, 
                    created_at, updated_at, last_login_at
                FROM public.users
                WHERE user_id = %s
            """, (user_id,))
            
            user = cursor.fetchone()
            
            if not user:
                return None
            
            return {
                "user_id": user["user_id"],
                "email": user["email"],
                "display_name": user["display_name"],
                "is_active": user["is_active"],
                "is_verified": user["is_verified"],
                "created_at": user["created_at"],
                "updated_at": user["updated_at"],
                "last_login_at": user["last_login_at"]
            }
            
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None
        finally:
            close_db_connection(conn, cursor)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        メールアドレス指定でユーザー情報取得
        
        Args:
            email: メールアドレス
        
        Returns:
            ユーザー情報 or None
        """
        conn = None
        cursor = None
        
        try:
            conn, cursor = get_db_connection()
            
            cursor.execute("""
                SELECT 
                    user_id, email, display_name, 
                    is_active, is_verified, 
                    created_at, updated_at, last_login_at
                FROM public.users
                WHERE email = %s
            """, (email,))
            
            user = cursor.fetchone()
            
            if not user:
                return None
            
            return {
                "user_id": user["user_id"],
                "email": user["email"],
                "display_name": user["display_name"],
                "is_active": user["is_active"],
                "is_verified": user["is_verified"],
                "created_at": user["created_at"],
                "updated_at": user["updated_at"],
                "last_login_at": user["last_login_at"]
            }
            
        except Exception as e:
            logger.error(f"Get user by email error: {e}")
            return None
        finally:
            close_db_connection(conn, cursor)
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """
        ユーザーのロール一覧取得
        
        Args:
            user_id: ユーザーID
        
        Returns:
            ロール名リスト
        """
        conn = None
        cursor = None
        
        try:
            conn, cursor = get_db_connection()
            
            cursor.execute("""
                SELECT r.role_name
                FROM public.user_roles ur
                JOIN public.roles r ON ur.role_id = r.role_id
                WHERE ur.user_id = %s
                  AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
            """, (user_id,))
            
            roles = cursor.fetchall()
            
            return [row["role_name"] for row in roles]
            
        except Exception as e:
            logger.error(f"Get user roles error: {e}")
            return []
        finally:
            close_db_connection(conn, cursor)
    
    def _log_audit(
        self,
        user_id: str,
        action: str,
        details: Dict[str, Any],
        status: str = "success"
    ):
        """
        監査ログ記録
        
        Args:
            user_id: ユーザーID
            action: アクション
            details: 詳細情報
            status: ステータス
        """
        conn = None
        cursor = None
        
        try:
            conn, cursor = get_db_connection()
            
            cursor.execute("""
                INSERT INTO public.audit_logs (
                    user_id, action, status, details, created_at
                )
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (user_id, action, status, str(details)))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Audit log error: {e}")
        finally:
            close_db_connection(conn, cursor)


# シングルトンインスタンス
auth_service = AuthService()