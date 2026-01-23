"""
FastAPI メインアプリケーション（認証統合版）
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
    title=app_config['app']['name'],  # ← "Knowledge-AI-Bot"
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
    # Phase 1: 認証チェックなし（全ユーザーに公開）
    # Phase 2: ユーザーのアクセス権をチェック
    
    return {
        "domain": domain_config['domain'],
        "ui": domain_config.get('ui', {})
    }


@app.post("/api/chat/message")
async def chat_message(
    request: dict,
    current_user: dict = Depends(get_current_active_user)  # ← 認証必須
):
    """
    チャットメッセージ（非ストリーミング）
    
    認証が必要です。
    """
    query = request.get("message", "")
    
    if not query:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # ドメインアクセス権チェック
    # TODO: Phase 1では省略、Phase 2で実装
    
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
    チャット（ストリーミング）
    
    WebSocket接続時に認証トークンをクエリパラメータで受け取ります。
    例: ws://localhost:8000/ws/chat?token=<access_token>
    """
    await websocket.accept()
    
    # 認証チェック（Phase 1: 簡易実装）
    # TODO: Phase 2でより厳密な認証実装
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
    
    try:
        while True:
            data = await websocket.receive_json()
            query = data.get("message", "")
            
            if not query:
                await websocket.send_json({
                    "type": "error",
                    "message": "Message is required"
                })
                continue
            
            logger.info(f"Received message from {user['email']}: {query[:50]}...")
            
            try:
                result = agent.chat(query)
                response_text = result['response']
                
                # ストリーミング風に送信
                chunk_size = 20
                for i in range(0, len(response_text), chunk_size):
                    chunk = response_text[i:i+chunk_size]
                    await websocket.send_json({
                        "type": "delta",
                        "content": chunk
                    })
                
                await websocket.send_json({"type": "done"})
                logger.info("Message processing completed")
                
            except Exception as e:
                logger.error(f"Error during message processing: {e}")
                import traceback
                logger.error(traceback.format_exc())
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {user['email']}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
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