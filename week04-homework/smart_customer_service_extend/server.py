"""FastAPI / Graph / Gradio 初始化"""
import uvicorn
from fastapi import FastAPI
import gradio as gr

from smart_customer_service_extend.api.chat_api import router as chat_router
from smart_customer_service_extend.api.health_api import router as health_router
from smart_customer_service_extend.api_service import ApiService
from smart_customer_service_extend.utils import setup_logger
from smart_customer_service_extend.workflow.persistent_graph import (
    create_persistent_workflow_graph,
)


def create_fastapi_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title="智能客服系统 API",
        description="基于 LangGraph 的客服系统 Web 服务封装",
        version="1.0.0",
    )
    app.include_router(health_router)
    app.include_router(chat_router)
    return app


def create_graph():
    """创建持久化对话图"""
    return create_persistent_workflow_graph()


def create_gradio_app():
    """创建 Gradio 应用实例"""
    async def chat_fn(message: str, session_id: str):
        reply = await api_service.chat(
            user_id="gradio_user",
            session_id=session_id,
            message=message,
        )
        return reply

    with gr.Blocks(title="智能客服系统") as demo:
        gr.Markdown("## 智能客服系统")
        session_id = gr.Textbox(label="Session ID", value="gradio_session")
        message = gr.Textbox(label="Message")
        output = gr.Textbox(label="Reply")
        submit = gr.Button("Send")
        submit.click(chat_fn, inputs=[message, session_id], outputs=[output])

    return demo


# 单例实例
logger = setup_logger()
app = create_fastapi_app()
api_service = ApiService()
graph = create_graph()


def main() -> None:
    """启动入口"""
    uvicorn.run(app, host="0.0.0.0", port=8000)
