"""API 数据模型定义"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    """对话请求"""
    message: str
    session_id: str
    user_id: Optional[str] = "test_user"

class ChatResponse(BaseModel):
    """对话响应"""
    reply: str
    session_id: str
    mode: str

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    agent_mode: str
    llm_connected: bool
    db_connected: bool
    version: str = "1.0.0"
