"""
会話管理API
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging
from datetime import datetime
import uuid
import json 

from app.auth.dependencies import get_current_active_user
from app.core.db_utils import get_db_connection, close_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


# リクエストスキーマを追加
class CreateConversationRequest(BaseModel):
    domain: str
    title: Optional[str] = None


class UpdateConversationRequest(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None


# メッセージ保存用の関数
async def save_message_to_db(
    conversation_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict] = None
) -> str:
    """
    メッセージをデータベースに保存
    
    Args:
        conversation_id: 会話ID
        role: 'user' or 'assistant'
        content: メッセージ内容
        metadata: メタデータ（オプション）
    
    Returns:
        message_id: 保存されたメッセージID
    """
    conn = None
    cursor = None
    
    try:
        message_id = str(uuid.uuid4())
        conn, cursor = get_db_connection()
        
        cursor.execute("""
            INSERT INTO public.messages (
                message_id,
                conversation_id,
                role,
                content,
                metadata,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING message_id
        """, (
            message_id,
            conversation_id,
            role,
            content,
            json.dumps(metadata) if metadata else None
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        logger.info(f"Message saved: {message_id} in conversation {conversation_id}")
        
        return str(result["message_id"])
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Save message error: {e}")
        raise
    finally:
        close_db_connection(conn, cursor)


async def update_conversation_timestamp(conversation_id: str):
    """
    会話のupdated_atを更新
    
    Args:
        conversation_id: 会話ID
    """
    conn = None
    cursor = None
    
    try:
        conn, cursor = get_db_connection()
        
        cursor.execute("""
            UPDATE public.conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = %s
        """, (conversation_id,))
        
        conn.commit()
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Update conversation timestamp error: {e}")
    finally:
        close_db_connection(conn, cursor)


async def generate_conversation_title(first_message: str) -> str:
    """
    最初のメッセージから会話タイトルを生成
    
    Args:
        first_message: 最初のユーザーメッセージ
    
    Returns:
        生成されたタイトル（最大50文字）
    """
    # シンプルな実装: 最初の50文字を使用
    title = first_message.strip()
    
    if len(title) > 50:
        title = title[:47] + "..."
    
    return title if title else "新しい会話"

@router.get("")
async def get_conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    domain: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """
    会話一覧取得
    
    Args:
        limit: 取得件数（1-100）
        offset: オフセット
        domain: ドメインフィルター（オプション）
        current_user: 現在のユーザー
    
    Returns:
        会話一覧
    """
    conn = None
    cursor = None
    
    try:
        user_id = current_user["user_id"]
        
        conn, cursor = get_db_connection(user_id=user_id)
        
        # 会話一覧取得
        query = """
            SELECT 
                c.conversation_id,
                c.domain,
                c.title,
                c.is_pinned,
                c.is_archived,
                c.created_at,
                c.updated_at,
                COUNT(m.message_id) as message_count
            FROM public.conversations c
            LEFT JOIN public.messages m ON c.conversation_id = m.conversation_id
            WHERE c.user_id = %s
              AND c.is_archived = false
        """
        
        params = [user_id]
        
        # ドメインフィルター
        if domain:
            query += " AND c.domain = %s"
            params.append(domain)
        
        query += """
            GROUP BY c.conversation_id
            ORDER BY c.is_pinned DESC, c.updated_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        conversations = cursor.fetchall()
        
        # 総数取得
        count_query = """
            SELECT COUNT(*)
            FROM public.conversations
            WHERE user_id = %s AND is_archived = false
        """
        count_params = [user_id]
        
        if domain:
            count_query += " AND domain = %s"
            count_params.append(domain)
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()["count"]
        
        logger.info(f"Get conversations: user={user_id}, count={len(conversations)}, total={total}")
        
        return {
            "conversations": [
                {
                    "conversation_id": str(c["conversation_id"]),
                    "domain": c["domain"],
                    "title": c["title"],
                    "message_count": c["message_count"],
                    "is_pinned": c["is_pinned"],
                    "created_at": c["created_at"],
                    "updated_at": c["updated_at"]
                }
                for c in conversations
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }
        
    except Exception as e:
        logger.error(f"Get conversations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversations"
        )
    finally:
        close_db_connection(conn, cursor)


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    会話詳細取得
    
    Args:
        conversation_id: 会話ID
        current_user: 現在のユーザー
    
    Returns:
        会話詳細（メッセージ含む）
    """
    conn = None
    cursor = None
    
    try:
        user_id = current_user["user_id"]
        
        conn, cursor = get_db_connection(user_id=user_id)
        
        # 会話取得
        cursor.execute("""
            SELECT 
                conversation_id,
                user_id,
                domain,
                title,
                is_pinned,
                is_archived,
                created_at,
                updated_at
            FROM public.conversations
            WHERE conversation_id = %s AND user_id = %s
        """, (conversation_id, user_id))
        
        conversation = cursor.fetchone()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # メッセージ取得
        cursor.execute("""
            SELECT 
                message_id,
                role,
                content,
                created_at
            FROM public.messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC
        """, (conversation_id,))
        
        messages = cursor.fetchall()
        
        return {
            "conversation_id": str(conversation["conversation_id"]),
            "domain": conversation["domain"],
            "title": conversation["title"],
            "is_pinned": conversation["is_pinned"],
            "is_archived": conversation["is_archived"],
            "created_at": conversation["created_at"],
            "updated_at": conversation["updated_at"],
            "messages": [
                {
                    "message_id": str(m["message_id"]),
                    "role": m["role"],
                    "content": m["content"],
                    "created_at": m["created_at"]
                }
                for m in messages
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation"
        )
    finally:
        close_db_connection(conn, cursor)


@router.post("")
async def create_conversation(
    request: CreateConversationRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    新規会話作成
    
    Args:
        request: 会話作成データ
        current_user: 現在のユーザー
    
    Returns:
        作成された会話
    """
    conn = None
    cursor = None
    
    try:
        user_id = current_user["user_id"]
        conversation_id = str(uuid.uuid4())
        
        conn, cursor = get_db_connection()
        
        # ドメインアクセス権確認
        cursor.execute("""
            SELECT status
            FROM public.user_domain_access
            WHERE user_id = %s AND domain_id = %s AND status = 'active'
        """, (user_id, request.domain))
        
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Domain access denied"
            )
        
        # 会話作成
        cursor.execute("""
            INSERT INTO public.conversations (
                conversation_id,
                user_id,
                domain,
                title,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING conversation_id, domain, title, created_at, updated_at
        """, (conversation_id, user_id, request.domain, request.title or "新しい会話"))
        
        result = cursor.fetchone()
        conn.commit()
        
        logger.info(f"Conversation created: {conversation_id}")
        
        return {
            "conversation_id": str(result["conversation_id"]),
            "domain": result["domain"],
            "title": result["title"],
            "created_at": result["created_at"],
            "updated_at": result["updated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Create conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )
    finally:
        close_db_connection(conn, cursor)


@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest,  # ← Pydanticモデルを使用
    current_user: dict = Depends(get_current_active_user)
):
    """
    会話更新（タイトル、ピン留め）
    """
    conn = None
    cursor = None
    
    try:
        user_id = current_user["user_id"]
        
        conn, cursor = get_db_connection(user_id=user_id)
        
        # 所有権確認
        cursor.execute("""
            SELECT conversation_id
            FROM public.conversations
            WHERE conversation_id = %s AND user_id = %s
        """, (conversation_id, user_id))
        
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # 更新
        updates = []
        params = []
        
        if request.title is not None:
            updates.append("title = %s")
            params.append(request.title)
        
        if request.is_pinned is not None:
            updates.append("is_pinned = %s")
            params.append(request.is_pinned)
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(conversation_id)
        params.append(user_id)
        
        query = f"""
            UPDATE public.conversations
            SET {', '.join(updates)}
            WHERE conversation_id = %s AND user_id = %s
            RETURNING conversation_id, title, is_pinned, updated_at
        """
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.commit()
        
        logger.info(f"Conversation updated: {conversation_id}")
        
        return {
            "conversation_id": str(result["conversation_id"]),
            "title": result["title"],
            "is_pinned": result["is_pinned"],
            "updated_at": result["updated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Update conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation"
        )
    finally:
        close_db_connection(conn, cursor)


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    会話削除（論理削除: is_archived=true）
    
    Args:
        conversation_id: 会話ID
        current_user: 現在のユーザー
    
    Returns:
        成功メッセージ
    """
    conn = None
    cursor = None
    
    try:
        user_id = current_user["user_id"]
        
        conn, cursor = get_db_connection(user_id=user_id)
        
        # 論理削除
        cursor.execute("""
            UPDATE public.conversations
            SET is_archived = true, updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = %s AND user_id = %s
            RETURNING conversation_id
        """, (conversation_id, user_id))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        conn.commit()
        
        logger.info(f"Conversation deleted: {conversation_id}")
        
        return {"message": "Conversation deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Delete conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )
    finally:
        close_db_connection(conn, cursor)