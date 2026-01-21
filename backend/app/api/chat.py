"""
チャットAPIエンドポイント
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.core.agent import get_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """チャットリクエスト"""
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    """チャットレスポンス"""
    response: str
    tool_calls: List[Dict[str, Any]] = []
    usage: Optional[Dict[str, Any]] = None
    timestamp: str


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """チャットエンドポイント"""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")
    
    logger.info(f"Received chat request: {request.message[:100]}...")
    
    try:
        # エージェント取得（遅延初期化）
        agent = get_agent()
        
        # エージェント実行
        result = agent.chat(
            user_message=request.message,
            conversation_history=request.conversation_history
        )
        
        return ChatResponse(
            response=result['response'],
            tool_calls=result.get('tool_calls', []),
            usage=result.get('usage'),
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.get("/health")
async def chat_health():
    """チャット機能のヘルスチェック"""
    try:
        # エージェント取得
        agent = get_agent()
        
        # 簡単なテストメッセージ
        result = agent.chat("こんにちは")
        return {
            "status": "healthy",
            "agent": agent.domain_config['agent']['name'],
            "model": agent.model,
            "test_response_length": len(result['response'])
        }
    except Exception as e:
        logger.error(f"Chat health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }