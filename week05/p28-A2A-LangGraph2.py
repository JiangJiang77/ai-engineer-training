import logging
import os
import sys
from typing import List, AsyncGenerator

import click
import httpx
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Message, TextPart, Role
import uuid
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv

# 导入我们之前创建的SearchAgent
from p28_A2A_LangGraph import SearchAgent, ResponseFormat

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


class SearchAgentExecutor(AgentExecutor):
    """SearchAgent的执行器，适配 A2A 接口"""

    def __init__(self, agent: SearchAgent):
        self.agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """执行搜索任务"""
        # 获取用户输入的文本内容
        query = context.get_user_input()
        session_id = context.task_id or "default_session"

        # 调用底层的 SearchAgent
        response_text = self.agent.invoke(query, session_id)

        # 封装为 A2A 协议要求的 Message 对象
        message = Message(
            role=Role.agent,
            message_id=f"msg_{uuid.uuid4()}",
            parts=[TextPart(text=response_text)],
            task_id=context.task_id,
        )

        # 将结果放入事件队列返回给客户端
        await event_queue.enqueue_event(message)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """取消任务（当前暂不支持）"""
        pass


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10001)
def main(host, port):
    """启动搜索Agent服务器"""
    try:
        # 检查必要的API密钥
        if not os.getenv("TAVILY_API_KEY"):
            raise MissingAPIKeyError("TAVILY_API_KEY environment variable not set.")

        if os.getenv("model_source", "google") == "google":
            if not os.getenv("GOOGLE_API_KEY"):
                raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")
        else:
            api_key_name = os.getenv("API_KEY_NAME", "API_KEY")
            if not os.getenv(api_key_name):
                raise MissingAPIKeyError(
                    f"{api_key_name} environment variable not set."
                )
            if not os.getenv("TOOL_LLM_URL"):
                raise MissingAPIKeyError("TOOL_LLM_URL environment variable not set.")
            if not os.getenv("TOOL_LLM_NAME"):
                raise MissingAPIKeyError("TOOL_LLM_NAME environment variable not set.")

        # 配置Agent能力
        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)

        # 定义搜索技能
        skill = AgentSkill(
            id="search_web",
            name="搜索工具",
            description="搜索web上的相关信息",
            tags=["Web搜索", "互联网搜索"],
            examples=["请搜索最新的黑神话悟空的消息"],
        )

        # 定义Agent卡片
        agent_card = AgentCard(
            name="搜索助手",
            description="搜索Web上的相关信息",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=SearchAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=SearchAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        # 初始化Agent和执行器
        search_agent = SearchAgent()
        agent_executor = SearchAgentExecutor(search_agent)

        # 配置HTTP客户端和推送通知
        httpx_client = httpx.AsyncClient()
        push_config_store = InMemoryPushNotificationConfigStore()
        push_sender = BasePushNotificationSender(
            httpx_client=httpx_client, config_store=push_config_store
        )

        # 创建请求处理器
        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=InMemoryTaskStore(),
            push_config_store=push_config_store,
            push_sender=push_sender,
        )

        # 创建A2A服务器
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )

        logger.info(f"正在启动服务器，地址：{host}:{port}")
        uvicorn.run(server.build(), host=host, port=port)

    except MissingAPIKeyError as e:
        logger.error(f"错误：{e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"服务器启动过程中发生错误：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
