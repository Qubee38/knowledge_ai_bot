"""
FastAPI メインアプリケーション（認証統合版 + メッセージ保存対応）
"""
from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
import json

from app.core.config import app_settings, config_loader
from app.core.agent_factory import AgentFactory
from app.core.tool_loader import ToolLoader
from app.auth.dependencies import get_current_active_user, optional_current_user

# APIルーター
from app.api import auth, domains, conversations

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 設定読み込み
app_config = config_loader.load_app_config()
domain_config = config_loader.get_active_domain_config()

# FastAPIアプリ
app = FastAPI(
    title=app_config['app']['name'],
    version=app_config['app']['version'],
    description=domain_config['domain']['description']
)

# CORS設定（設定ファイルから読み込み）
cors_config = app_config.get('cors', {})
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.get('allow_origins', ["*"]),
    allow_credentials=cors_config.get('allow_credentials', True),
    allow_methods=cors_config.get('allow_methods', ["*"]),
    allow_headers=cors_config.get('allow_headers', ["*"]),
)

# APIルーター登録
app.include_router(auth.router)
app.include_router(domains.router)
app.include_router(conversations.router)

# ツールローダー初期化
tool_loader = ToolLoader(config_loader)
tools = tool_loader.load_tools()
tool_functions = tool_loader.get_tool_functions()

# エージェントファクトリ初期化
agent_factory = AgentFactory(config_loader, app_settings)

# エージェント生成
agent = agent_factory.create_agent(
    tools=tools,
    tool_functions=tool_functions
)

logger.info(f"App: {app_config['app']['name']}")
logger.info(f"Active Domain: {domain_config['domain']['name']}")
logger.info(f"Agent: {agent.name}")
logger.info(f"Tools loaded: {len(tools)}")


@app.get("/")
def root():
    """ルート（認証不要）"""
    return {
        "app": app_config['app']['name'],
        "version": app_config['app']['version'],
        "domain": domain_config['domain']['name'],
        "agent": agent.name,
        "tools": len(tools),
        "status": "running"
    }


@app.get("/api/health")
def health_check():
    """ヘルスチェック（認証不要）"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "domain": domain_config['domain']['id'],
        "agent": agent.name
    }


@app.get("/api/config/domain")
def get_domain_config(current_user: dict = Depends(optional_current_user)):
    """
    ドメイン設定取得（認証オプション）
    
    認証されている場合、ユーザーのアクセス可能ドメインを考慮します。
    """
    return {
        "domain": domain_config['domain'],
        "ui": domain_config.get('ui', {})
    }


@app.post("/api/chat/message")
async def chat_message(
    request: dict,
    current_user: dict = Depends(get_current_active_user)
):
    """
    チャットメッセージ（非ストリーミング）
    
    認証が必要です。
    """
    query = request.get("message", "")
    
    if not query:
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        result = agent.chat(query)
        
        return {
            "response": result['response'],
            "tool_calls": result.get('tool_calls', []),
            "usage": result.get('usage'),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    チャット（ストリーミング + メッセージ保存）
    
    WebSocket接続時に認証トークンをクエリパラメータで受け取ります。
    例: ws://localhost:8000/ws/chat?token=<access_token>
    """
    await websocket.accept()
    
    # ===== 認証チェック =====
    query_params = websocket.query_params
    token = query_params.get('token')
    
    if not token:
        await websocket.send_json({
            "type": "error",
            "message": "Authentication required. Please provide token in query parameter."
        })
        await websocket.close(code=1008)  # Policy Violation
        return
    
    # トークン検証
    from app.core.security import verify_token
    from app.auth.service import auth_service
    import uuid
    
    payload = verify_token(token, token_type="access")
    if not payload:
        await websocket.send_json({
            "type": "error",
            "message": "Invalid or expired token"
        })
        await websocket.close(code=1008)
        return
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        await websocket.send_json({
            "type": "error",
            "message": "Invalid token payload"
        })
        await websocket.close(code=1008)
        return
    
    user_id = uuid.UUID(user_id_str)
    user = auth_service.get_user_by_id(user_id)
    
    if not user or not user.get('is_active'):
        await websocket.send_json({
            "type": "error",
            "message": "User not found or inactive"
        })
        await websocket.close(code=1008)
        return
    
    logger.info(f"WebSocket connection accepted for user: {user['email']}")
    
    # ===== メッセージ保存ヘルパーインポート =====
    from app.utils.message_helpers import (
        save_user_message,
        save_assistant_message,
        update_conversation_title_if_needed,
        get_conversation_messages
    )
    
    try:
        while True:
            # ===== メッセージ受信 =====
            data = await websocket.receive_json()
            query = data.get("message", "")
            conversation_id = data.get("conversation_id")
            
            # バリデーション
            if not query:
                await websocket.send_json({
                    "type": "error",
                    "message": "Message is required"
                })
                continue
            
            if not conversation_id:
                await websocket.send_json({
                    "type": "error",
                    "message": "conversation_id is required"
                })
                continue
            
            logger.info(f"Received message from {user['email']}: {query[:50]}...")
            logger.info(f"Conversation ID: {conversation_id}")
            
            try:
                # ===== Step 1: ユーザーメッセージ保存 =====
                user_message_id = save_user_message(
                    conversation_id=conversation_id,
                    user_id=str(user_id),
                    content=query
                )
                logger.info(f"✅ User message saved: {user_message_id}")
                
                # ===== Step 2: 過去メッセージ取得（会話履歴） =====
                conversation_history = get_conversation_messages(
                    conversation_id=conversation_id,
                    user_id=str(user_id),
                    limit=10  # 直近10件
                )
                logger.info(f"📜 Loaded {len(conversation_history)} past messages")
                
                # ===== Step 3: AIエージェント実行（ストリーミング） =====
                accumulated_response = ""
                tool_calls_info = []
                
                logger.info("🤖 Starting agent chat stream...")
                
                for event in agent.chat_stream(query, conversation_history=conversation_history):
                    event_type = event.get("type")
                    
                    if event_type == "delta":
                        # テキストチャンクをクライアントに送信
                        content = event.get("content", "")
                        accumulated_response += content
                        
                        await websocket.send_json({
                            "type": "delta",
                            "content": content
                        })
                    
                    elif event_type == "tool_calls_start":
                        # ツール呼び出し開始通知
                        logger.info(f"🔧 Tool calls started: {len(event.get('tool_calls', []))}")
                        await websocket.send_json({
                            "type": "tool_calls_start",
                            "count": len(event.get('tool_calls', []))
                        })
                    
                    elif event_type == "tool_call":
                        # ツール呼び出し通知
                        tool_name = event.get("tool_name")
                        logger.info(f"🔧 Calling tool: {tool_name}")
                        
                        await websocket.send_json({
                            "type": "tool_call",
                            "tool_name": tool_name,
                            "arguments": event.get("arguments")
                        })
                    
                    elif event_type == "tool_result":
                        # ツール結果通知
                        tool_name = event.get("tool_name")
                        logger.info(f"✅ Tool result: {tool_name}")
                        
                        await websocket.send_json({
                            "type": "tool_result",
                            "tool_name": tool_name
                        })
                    
                    elif event_type == "done":
                        # ストリーミング完了
                        accumulated_response = event.get("response", accumulated_response)
                        tool_calls_info = event.get("tool_calls", [])
                        
                        logger.info("✅ Streaming completed")
                        logger.info(f"📝 Response length: {len(accumulated_response)}")
                        logger.info(f"🔧 Tool calls: {len(tool_calls_info)}")
                        
                        # ===== Step 4: アシスタントメッセージ保存 =====
                        metadata = {
                            "model": agent.model,
                            "tool_calls": tool_calls_info
                        }
                        
                        assistant_message_id = save_assistant_message(
                            conversation_id=conversation_id,
                            user_id=str(user_id),
                            content=accumulated_response,
                            metadata=metadata
                        )
                        logger.info(f"✅ Assistant message saved: {assistant_message_id}")
                        
                        # ===== Step 5: 会話タイトル自動生成（初回のみ）=====
                        title_updated = update_conversation_title_if_needed(
                            conversation_id=conversation_id,
                            user_id=str(user_id),
                            first_message=query
                        )
                        if title_updated:
                            logger.info("📝 Conversation title auto-generated")
                        
                        # ===== Step 6: 完了通知 =====
                        await websocket.send_json({
                            "type": "done",
                            "user_message_id": user_message_id,
                            "assistant_message_id": assistant_message_id,
                            "conversation_id": conversation_id
                        })
                        
                        logger.info("🎉 Message processing completed successfully")
                        break
                    
                    elif event_type == "error":
                        # エラー発生
                        error_message = event.get("message", "Unknown error")
                        logger.error(f"❌ Agent error: {error_message}")
                        
                        await websocket.send_json({
                            "type": "error",
                            "message": error_message
                        })
                        break
                
            except Exception as e:
                logger.error(f"❌ Error during message processing: {e}")
                import traceback
                logger.error(traceback.format_exc())
                
                await websocket.send_json({
                    "type": "error",
                    "message": f"処理中にエラーが発生しました: {str(e)}"
                })
    
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected for user: {user['email']}")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )