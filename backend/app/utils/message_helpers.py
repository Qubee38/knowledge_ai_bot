"""
メッセージ保存・管理ヘルパー関数
"""
import logging
import uuid
import json
import re
from typing import Optional, Dict
from app.core.db_utils import get_db_connection, close_db_connection

logger = logging.getLogger(__name__)


def generate_conversation_title(message: str, max_length: int = 30) -> str:
    """
    メッセージから会話タイトルを生成
    
    Args:
        message: ユーザーメッセージ
        max_length: 最大文字数（デフォルト30）
    
    Returns:
        生成されたタイトル
    """
    # 改行・余分な空白を削除
    cleaned = re.sub(r'\s+', ' ', message.strip())
    
    # 最大文字数で切り取り
    if len(cleaned) <= max_length:
        return cleaned
    
    # 30文字で切って "..." を追加
    return cleaned[:max_length] + "..."


def save_user_message(
    conversation_id: str,
    user_id: str,
    content: str
) -> str:
    """
    ユーザーメッセージをDB保存
    
    Args:
        conversation_id: 会話ID
        user_id: ユーザーID
        content: メッセージ内容
    
    Returns:
        message_id: 生成されたメッセージID
    
    Raises:
        Exception: DB保存失敗時
    """
    conn = None
    cursor = None
    
    try:
        conn, cursor = get_db_connection(user_id=user_id)
        
        message_id = uuid.uuid4()
        
        cursor.execute("""
            INSERT INTO messages (
                message_id,
                conversation_id,
                role,
                content,
                created_at
            ) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING message_id
        """, (message_id, conversation_id, 'user', content))
        
        result = cursor.fetchone()
        
        # conversations.updated_at を更新
        cursor.execute("""
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = %s
        """, (conversation_id,))
        
        conn.commit()
        logger.info(f"Saved user message: {message_id}")
        
        return str(result['message_id'])
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Failed to save user message: {e}")
        raise
    finally:
        close_db_connection(conn, cursor)


def save_assistant_message(
    conversation_id: str,
    user_id: str,
    content: str,
    metadata: Optional[Dict] = None
) -> str:
    """
    アシスタントメッセージをDB保存
    
    Args:
        conversation_id: 会話ID
        user_id: ユーザーID
        content: メッセージ内容
        metadata: メタデータ（model, tool_calls等）
    
    Returns:
        message_id: 生成されたメッセージID
    
    Raises:
        Exception: DB保存失敗時
    """
    conn = None
    cursor = None
    
    try:
        conn, cursor = get_db_connection(user_id=user_id)
        
        message_id = uuid.uuid4()
        
        cursor.execute("""
            INSERT INTO messages (
                message_id,
                conversation_id,
                role,
                content,
                metadata,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING message_id
        """, (
            message_id,
            conversation_id,
            'assistant',
            content,
            json.dumps(metadata, ensure_ascii=False) if metadata else None
        ))
        
        result = cursor.fetchone()
        
        # conversations.updated_at を更新
        cursor.execute("""
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = %s
        """, (conversation_id,))
        
        conn.commit()
        logger.info(f"Saved assistant message: {message_id}")
        
        return str(result['message_id'])
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Failed to save assistant message: {e}")
        raise
    finally:
        close_db_connection(conn, cursor)


def update_conversation_title_if_needed(
    conversation_id: str,
    user_id: str,
    first_message: str
) -> bool:
    """
    会話タイトルを自動生成（初回メッセージのみ）
    
    Args:
        conversation_id: 会話ID
        user_id: ユーザーID
        first_message: 最初のユーザーメッセージ
    
    Returns:
        bool: タイトル更新したかどうか
    """
    conn = None
    cursor = None
    
    try:
        conn, cursor = get_db_connection(user_id=user_id)
        
        # 会話のメッセージ数を確認
        cursor.execute("""
            SELECT COUNT(*) as message_count
            FROM messages
            WHERE conversation_id = %s
        """, (conversation_id,))
        
        result = cursor.fetchone()
        message_count = result['message_count'] if result else 0
        
        # 初回メッセージ（count=1: ユーザーメッセージのみ）の場合のみタイトル更新
        if message_count == 1:
            new_title = generate_conversation_title(first_message)
            
            cursor.execute("""
                UPDATE conversations
                SET 
                    title = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE conversation_id = %s
                  AND user_id = %s
            """, (new_title, conversation_id, user_id))
            
            conn.commit()
            logger.info(f"Updated conversation title: '{new_title}'")
            return True
        
        return False
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Failed to update conversation title: {e}")
        # タイトル生成失敗は致命的エラーではないのでログのみ
        return False
    finally:
        close_db_connection(conn, cursor)


def get_conversation_messages(
    conversation_id: str,
    user_id: str,
    limit: int = 50
) -> list:
    """
    会話の過去メッセージを取得
    
    Args:
        conversation_id: 会話ID
        user_id: ユーザーID
        limit: 最大取得件数
    
    Returns:
        list: メッセージリスト（OpenAI API形式）
    """
    conn = None
    cursor = None
    
    try:
        conn, cursor = get_db_connection(user_id=user_id)
        
        cursor.execute("""
            SELECT 
                message_id,
                role,
                content,
                created_at
            FROM messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC
            LIMIT %s
        """, (conversation_id, limit))
        
        messages = cursor.fetchall()
        
        # OpenAI API形式に変換
        return [
            {
                "role": msg['role'],
                "content": msg['content']
            }
            for msg in messages
        ]
        
    except Exception as e:
        logger.error(f"Failed to get conversation messages: {e}")
        return []
    finally:
        close_db_connection(conn, cursor)