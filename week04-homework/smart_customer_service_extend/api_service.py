"""API 服务层逻辑"""
import asyncio
from typing import AsyncGenerator, Dict, Any
from smart_customer_service_extend.agents import CustomerServiceReActAgent
from smart_customer_service_extend.workflow import run_workflow
from smart_customer_service_extend.config import settings
from smart_customer_service_extend.utils import get_logger

logger = get_logger(__name__)

class ApiService:
    """封装 Agent 调用逻辑"""
    
    def __init__(self):
        self.mode = settings.AGENT_MODE
        logger.info(f"初始化 ApiService, 模式: {self.mode}")

    def _resolve_user_id(self, user_id: str) -> str:
        """解析用户ID, 如果输入是用户名则转换为 UUID"""
        from smart_customer_service_extend.repository import get_user_by_username
        user = get_user_by_username(user_id)
        if user:
            logger.debug(f"[API] 解析用户: {user_id} -> {user['user_id']}")
            return user["user_id"]
        return user_id

    async def chat(self, user_id: str, session_id: str, message: str) -> str:
        """非流式对话"""
        user_id = self._resolve_user_id(user_id)
        if self.mode == "react":
            agent = CustomerServiceReActAgent(user_id)
            result = agent.run(message)
            return result["output"]
        else:
            # Workflow 模式
            # 注意: workflow 目前是同步运行的，我们可以用 run_in_executor 或者直接调用
            response = await asyncio.to_thread(run_workflow, user_id, session_id, message)
            return response

    async def chat_stream(self, user_id: str, session_id: str, message: str) -> AsyncGenerator[str, None]:
        """流式对话 (SSE)"""
        # 由于目前的 Agent/Workflow 并没有实现细粒度的流式输出，
        # 我们这里通过模拟或包装来实现符合 SSE 要求的生成器。
        # 在真实的 LangChain 方案中，可以使用 astream_events。
        
        user_id = self._resolve_user_id(user_id)
        logger.debug(f"开始流式处理: {message}")
        
        if self.mode == "react":
            agent = CustomerServiceReActAgent(user_id)
            # 暂时包装成一次性输出，模拟流式
            result = agent.run(message)
            yield result["output"]
        else:
            response = await asyncio.to_thread(run_workflow, user_id, session_id, message)
            yield response

    async def check_health(self) -> Dict[str, Any]:
        """健康检查"""
        # 简单检查 LLM 可用性
        llm_ok = False
        try:
            from langchain_community.chat_models import ChatTongyi
            llm = ChatTongyi(
                model=settings.LLM_MODEL,
                dashscope_api_key=settings.DASHSCOPE_API_KEY
            )
            # 尝试极简调用
            await asyncio.wait_for(llm.ainvoke("ping"), timeout=3.0)
            llm_ok = True
        except Exception as e:
            logger.error(f"健康检查 - LLM 失败: {e}")

        # 检查数据库
        db_ok = False
        try:
            from smart_customer_service_extend.repository import get_user_by_username
            # 尝试查询测试用户
            user = await asyncio.to_thread(get_user_by_username, "test_user")
            db_ok = user is not None
        except Exception as e:
            logger.error(f"健康检查 - 数据库失败: {e}")

        return {
            "status": "healthy" if llm_ok and db_ok else "unhealthy",
            "agent_mode": self.mode,
            "llm_connected": llm_ok,
            "db_connected": db_ok
        }
