"""
ドメインアクセス管理API
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
import logging
from datetime import datetime
import uuid

from app.auth.dependencies import get_current_active_user
from app.auth.schemas import DomainAccessRequest, DomainAccessResponse
from app.core.db_utils import get_db_connection, close_db_connection

logger = logging.getLogger(__name__)

# prefix末尾にスラッシュなし
router = APIRouter(prefix="/api/domains", tags=["Domains"])


# ルートは空文字列
@router.get("")
async def get_domains(current_user: dict = Depends(get_current_active_user)):
    """
    利用可能ドメイン一覧取得
    
    Args:
        current_user: 現在のユーザー
    
    Returns:
        ドメイン一覧
    """
    conn = None
    cursor = None
    
    try:
        user_id = current_user["user_id"]
        
        # DB接続
        conn, cursor = get_db_connection()
        
        # ユーザーのドメインアクセス情報取得
        cursor.execute("""
            SELECT 
                domain_id,
                status,
                requested_at,
                approved_at
            FROM public.user_domain_access
            WHERE user_id = %s
        """, (user_id,))
        
        user_access = {row["domain_id"]: row for row in cursor.fetchall()}
        
        # 利用可能なドメイン一覧（Phase 1では固定値）
        available_domains = [
            {
                "domain_id": "horse-racing",
                "name": "競馬ナレッジボット",
                "description": "レース傾向分析とデータドリブン推奨",
                "icon": "🏇"
            }
        ]
        
        # アクセス状態を付与
        domains = []
        for domain in available_domains:
            domain_id = domain["domain_id"]
            access_info = user_access.get(domain_id)
            
            if access_info:
                domain["access_status"] = access_info["status"]
                domain["requested_at"] = access_info["requested_at"]
                domain["approved_at"] = access_info["approved_at"]
            else:
                domain["access_status"] = "available"
                domain["requested_at"] = None
                domain["approved_at"] = None
            
            domains.append(domain)
        
        logger.info(f"Get domains for user: {user_id}, count: {len(domains)}")
        
        return {"domains": domains}
        
    except Exception as e:
        logger.error(f"Get domains error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get domains"
        )
    finally:
        close_db_connection(conn, cursor)


@router.post("/{domain_id}/request", response_model=DomainAccessResponse)
async def request_domain_access(
    domain_id: str,
    request: DomainAccessRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    ドメインアクセス申請（Phase 1: 自動承認）
    
    Args:
        domain_id: ドメインID
        request: 申請データ
        current_user: 現在のユーザー
    
    Returns:
        アクセス許可情報
    """
    conn = None
    cursor = None
    
    try:
        user_id = current_user["user_id"]
        
        # DB接続
        conn, cursor = get_db_connection()
        
        # 重複チェック
        cursor.execute("""
            SELECT access_id
            FROM public.user_domain_access
            WHERE user_id = %s AND domain_id = %s
        """, (user_id, domain_id))
        
        existing = cursor.fetchone()
        
        if existing:
            raise ValueError("Domain access already requested")
        
        # アクセス許可作成（Phase 1: 自動承認）
        access_id = str(uuid.uuid4())
        now = datetime.now()
        
        cursor.execute("""
            INSERT INTO public.user_domain_access (
                access_id,
                user_id,
                domain_id,
                status,
                requested_at,
                approved_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING access_id, domain_id, status, requested_at, approved_at
        """, (
            access_id,
            user_id,
            domain_id,
            "active",
            now,
            now
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        logger.info(f"Domain access granted: user={user_id}, domain={domain_id}")
        
        return {
            "access_id": result["access_id"],
            "domain_id": result["domain_id"],
            "status": result["status"],
            "requested_at": result["requested_at"],
            "approved_at": result["approved_at"]
        }
        
    except ValueError as e:
        logger.error(f"Domain access request validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Domain access request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request domain access"
        )
    finally:
        close_db_connection(conn, cursor)


@router.delete("/{domain_id}/access")
async def revoke_domain_access(
    domain_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    ドメインアクセス取り消し
    
    Args:
        domain_id: ドメインID
        current_user: 現在のユーザー
    
    Returns:
        成功メッセージ
    """
    conn = None
    cursor = None
    
    try:
        user_id = current_user["user_id"]
        
        # DB接続
        conn, cursor = get_db_connection()
        
        # アクセス削除
        cursor.execute("""
            DELETE FROM public.user_domain_access
            WHERE user_id = %s AND domain_id = %s
            RETURNING access_id
        """, (user_id, domain_id))
        
        result = cursor.fetchone()
        
        if not result:
            raise ValueError("Domain access not found")
        
        conn.commit()
        
        logger.info(f"Domain access revoked: user={user_id}, domain={domain_id}")
        
        return {"message": f"Access to {domain_id} revoked"}
        
    except ValueError as e:
        logger.error(f"Revoke domain access validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Revoke domain access error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke domain access"
        )
    finally:
        close_db_connection(conn, cursor)


@router.get("/check-access/{domain_id}")
async def check_domain_access(
    domain_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    ドメインアクセス権確認
    
    Args:
        domain_id: ドメインID
        current_user: 現在のユーザー
    
    Returns:
        アクセス権情報
    """
    conn = None
    cursor = None
    
    try:
        user_id = current_user["user_id"]
        
        # DB接続
        conn, cursor = get_db_connection()
        
        # アクセス権確認
        cursor.execute("""
            SELECT status
            FROM public.user_domain_access
            WHERE user_id = %s AND domain_id = %s
        """, (user_id, domain_id))
        
        result = cursor.fetchone()
        
        if result and result["status"] == "active":
            return {
                "has_access": True,
                "status": result["status"]
            }
        else:
            return {
                "has_access": False,
                "status": result["status"] if result else None
            }
        
    except Exception as e:
        logger.error(f"Check domain access error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check domain access"
        )
    finally:
        close_db_connection(conn, cursor)