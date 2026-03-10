import os
from .tool import default_tools
from langchain_community.chat_models import ChatTongyi


class ServiceManager:
    """
    llm&tools服务管理器
    """
    def __init__(self):
        self._llm = self._create_llm()
        self._tools = default_tools
        self.print_service_status()

    def _create_llm(self,
                    model_name: str | None = None,
                    temperature: float = 0,
                    streaming: bool = False ):
        if not os.environ.get("DASHSCOPE_API_KEY"):
            print("⚠️ 警告: DASHSCOPE_API_KEY 环境变量未设置！")
        print(f"🤖 加载LLM: {model_name},temperature: {temperature},streaming: {streaming}")
        return ChatTongyi(
            model_name = model_name or "qwen-plus",
            temperature = temperature,
            streaming = streaming,
        )

    def get_llm(self):
        return self._llm

    def update_llm(self,model_name: str | None = None,
                    temperature: float = 0,
                    streaming: bool = False ):
        self._llm = self._create_llm(model_name,temperature,streaming)
        print("🤖 LLM 重新加载完成")
        print(f"🤖 LLM: {self._llm.model_name},温度: {self._llm.temperature},流式: {self._llm.streaming}")

    def get_tools(self):
        return self._tools

    def update_tools(self,new_tools: list):
        self._tools = new_tools
        print("🤖 工具重新加载完成")
        print(f"🤖 工具: {self._tools}")

    def print_service_status(self):
        print("🤖 服务状态:")
        print(f"🤖 LLM: {self._llm.model_name}")
        print(f"🤖 工具: {[tool.name for tool in self._tools]}")

    def get_service_status(self):
        return {
            "llm": {
                "model_name": self._llm.model_name,
                "temperature": self._llm.temperature,
                "streaming": self._llm.streaming,
            },
            "tools": [tool.name for tool in self._tools],
        }

# 创建一个单例
service_manager = ServiceManager()