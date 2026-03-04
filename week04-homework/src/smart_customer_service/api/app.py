"""FastAPI 主应用"""
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from smart_customer_service.api.models import ChatRequest, ChatResponse, HealthResponse
from smart_customer_service.api.service import ApiService
from smart_customer_service.config import settings
from smart_customer_service.utils import setup_logger
import asyncio

# 初始化日志
logger = setup_logger()

app = FastAPI(
    title="智能客服系统 API",
    description="基于 LangGraph 的客服系统 Web 服务封装",
    version="1.0.0"
)

# 初始化服务层
api_service = ApiService()

@app.get("/health", response_model=HealthResponse)
async def health():
    """健康检查接口"""
    health_status = await api_service.check_health()
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    return health_status

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """标准 HTTP 对话接口"""
    try:
        reply = await api_service.chat(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message
        )
        return ChatResponse(
            reply=reply,
            session_id=request.session_id,
            mode=settings.AGENT_MODE
        )
    except Exception as e:
        logger.error(f"Chat 接口错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/stream")
async def chat_stream(message: str, session_id: str, user_id: str = "test_user"):
    """SSE 流式对话接口"""
    async def event_generator():
        try:
            async for chunk in api_service.chat_stream(user_id, session_id, message):
                # SSE 格式: data: <content>
                yield {"data": chunk}
        except Exception as e:
            logger.error(f"Stream 接口错误: {e}", exc_info=True)
            yield {"data": f"Error: {str(e)}", "event": "error"}

    return EventSourceResponse(event_generator())

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, user_id: str = "test_user"):
    """WebSocket 对话接口"""
    await websocket.accept()
    logger.info(f"WebSocket 连接已建立: session_id={session_id}")
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            logger.debug(f"WebSocket 收到消息: {data}")
            
            # 这里简单起见，调用现有的 api_service.chat_stream
            # 如果需要完美的打字机效果，可以在 service 层做进一步封装
            async for chunk in api_service.chat_stream(user_id, session_id, data):
                await websocket.send_text(chunk)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket 连接已断开: session_id={session_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}", exc_info=True)
        await websocket.close(code=1011)

if __name__ == "__main__":
    # 启动命令: python -m smart_customer_service.api.app
    uvicorn.run(app, host="0.0.0.0", port=8000)
