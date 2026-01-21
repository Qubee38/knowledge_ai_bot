"""
FastAPI メインアプリケーション（テンプレート化版）
AgentFactory + ToolLoader を使用した動的エージェント生成
"""
from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
import json

from app.core.config import app_settings, config_loader
from app.core.agent_factory import AgentFactory
from app.core.tool_loader import ToolLoader

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
    title=domain_config['domain']['name'],
    version=domain_config['domain']['version'],
    description=domain_config['domain']['description']
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発環境では全て許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

logger.info(f"Active Domain: {domain_config['domain']['name']}")
logger.info(f"Agent: {agent.name}")
logger.info(f"Tools loaded: {len(tools)}")


@app.get("/")
def root():
    """ルート"""
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
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "domain": domain_config['domain']['id'],
        "agent": agent.name
    }


@app.get("/api/config/domain")
def get_domain_config():
    """ドメイン設定取得（Frontend用）"""
    return {
        "domain": domain_config['domain'],
        "ui": domain_config.get('ui', {})
    }


@app.post("/api/chat/message")
async def chat_message(request: dict):
    """チャットメッセージ（非ストリーミング）"""
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
    """チャット（ストリーミング）"""
    # WebSocket接続を受け入れる
    await websocket.accept()
    logger.info(f"WebSocket connection accepted from {websocket.client}")
    
    try:
        while True:
            # クライアントからメッセージ受信
            data = await websocket.receive_json()
            query = data.get("message", "")
            
            if not query:
                await websocket.send_json({
                    "type": "error",
                    "message": "Message is required"
                })
                continue
            
            logger.info(f"Received message: {query[:50]}...")
            
            try:
                # エージェント実行
                result = agent.chat(query)
                
                # レスポンスを送信（一括）
                response_text = result['response']
                
                # チャンク分割してストリーミング風に送信
                chunk_size = 20  # 文字数
                for i in range(0, len(response_text), chunk_size):
                    chunk = response_text[i:i+chunk_size]
                    await websocket.send_json({
                        "type": "delta",
                        "content": chunk
                    })
                
                # 完了通知
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
        logger.info(f"WebSocket disconnected from {websocket.client}")
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