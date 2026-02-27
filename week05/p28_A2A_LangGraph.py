import os
from dotenv import load_dotenv

load_dotenv()
from collections.abc import AsyncIterable
from typing import Any, Dict, Literal
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from tavily import TavilyClient

# 初始化内存存储
memory = MemorySaver()


@tool
def search_tavily(query: str, search_depth: str = "basic") -> Dict[str, Any]:
    """使用Tavily进行网络搜索

    Args:
        query: 搜索查询字符串
        search_depth: 搜索深度，"basic" 或 "advanced"

    Returns:
        包含搜索结果或错误信息的字典
    """
    try:
        tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

        if search_depth == "advanced":
            result = tavily_client.search(query, depth="advanced", include_answer=True)
        else:
            result = tavily_client.search(query, include_answer=True)

        return {
            "success": True,
            "results": result.get("results", []),
            "answer": result.get("answer", ""),
            "query": query,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class ResponseFormat(BaseModel):
    """以这种格式回应用户"""

    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str


class SearchAgent:
    """搜索Agent - 专门进行网络搜索的助手"""

    # 支持的输入输出类型
    SUPPORTED_CONTENT_TYPES = ["text/plain"]

    SYSTEM_INSTRUCTION = (
        "你是一个专门进行网络搜索的助手。"
        "你的主要目的是使用'search_tavily'工具来回答用户问题，提供最新、最相关的信息。"
        "如果需要用户提供更多信息来进行有效搜索，将响应状态设置为input_required。"
        "如果处理请求时发生错误，将响应状态设置为error。"
        "如果请求已完成并提供了答案，将响应状态设置为completed。"
    )

    def __init__(self):
        model_source = os.getenv("model_source", "google")

        # 为 Qwen 系列模型添加特定的 JSON 格式指令，以满足 API 合规性要求
        full_prompt = self.SYSTEM_INSTRUCTION
        llm_name = os.getenv("TOOL_LLM_NAME", "gpt-4")
        if llm_name.lower().startswith("qwen"):
            full_prompt += "\n重要：请务必以 json 格式返回响应，确保包含 'status' 和 'message' 两个字段。"

        if model_source == "google":
            self.model = ChatGoogleGenerativeAI(
                model="gemini-3-flash-preview",
                api_key=os.getenv("GOOGLE_API_KEY"),
            )
        else:
            api_key_name = os.getenv("API_KEY_NAME", "API_KEY")
            self.model = ChatOpenAI(
                model=os.getenv("TOOL_LLM_NAME", "gpt-4"),
                openai_api_key=os.getenv(api_key_name, "EMPTY"),
                openai_api_base=os.getenv("TOOL_LLM_URL"),
                temperature=0,
            )
        self.tools = [search_tavily]

        self.graph = create_react_agent(
            self.model,
            tools=self.tools,
            checkpointer=memory,
            prompt=full_prompt,
            response_format=ResponseFormat,
        )

    def invoke(self, query: str, sessionId: str) -> str:
        """同步调用搜索Agent"""
        # 为 Qwen 系列模型在 query 中添加 json 提示，增强稳定性
        llm_name = os.getenv("TOOL_LLM_NAME", "gpt-4")
        if llm_name.lower().startswith("qwen") and "json" not in query.lower():
            query += " (请用json格式回答)"

        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": sessionId}}

        print("inputs: ", inputs)
        print("config: ", config)
        result = self.graph.invoke(inputs, config)
        print("result: ", result)
        return self._format_response(result, config)

    async def stream(self, query: str, sessionId: str) -> AsyncIterable[Dict[str, Any]]:
        """异步流式搜索"""
        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": sessionId}}

        async for item in self.graph.astream(inputs, config, stream_mode="values"):
            message = item["messages"][-1]
            if hasattr(message, "tool_calls") and message.tool_calls:
                yield {"status": "processing", "message": "正在搜索网络信息..."}
            elif hasattr(message, "content"):
                yield {"status": "processing", "message": message.content}

        final_result = self._get_agent_response(config)
        yield final_result

    def _get_agent_response(self, config):
        """获取最终的Agent响应"""
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get("structured_response")

        if structured_response and isinstance(structured_response, ResponseFormat):
            return {
                "status": structured_response.status,
                "message": structured_response.message,
            }

        return {"status": "error", "message": "无法处理请求，请稍后重试"}

    def _format_response(self, result, config):
        """格式化响应"""
        response = self._get_agent_response(config)
        return f"Status: {response['status']}\nMessage: {response['message']}"


# 使用示例
if __name__ == "__main__":
    # 设置环境变量
    # os.environ["TAVILY_API_KEY"] = "your_tavily_api_key_here"

    agent = SearchAgent()
    result = agent.invoke("最新的AI技术发展", "test_session")
    print(result)
