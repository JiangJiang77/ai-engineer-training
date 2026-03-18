import os
from typing import List

from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import BaseMessage

class LLMClient:
    def __init__(self) -> None:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        self._enabled = bool(api_key)
        self._llm = None
        if self._enabled:
            self._llm = ChatTongyi(
                model="qwen-plus",
                temperature=0.1,  # 低温度保证稳定性
                dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
            )

    def generate(
        self,
        prompt: List[BaseMessage]
    ) -> str:
        if not prompt:
            raise ValueError("prompt cannot be empty")
        if not all(isinstance(item, BaseMessage) for item in prompt):
            raise ValueError("prompt must be a Message array")
        if not self._enabled:
            raise RuntimeError("LLM is unavailable: DASHSCOPE_API_KEY is not set")
        try:
            response = self._llm.invoke(prompt)
            content = response.content
            if isinstance(content, str):
                return content
            return str(content)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"LLM generate failed: {exc}") from exc


llm_client = LLMClient()
