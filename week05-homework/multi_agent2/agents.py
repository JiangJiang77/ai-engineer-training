import os
import random
from typing import List, Annotated, TypedDict, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

# 加载环境变量 (参考 week05/.env)
load_dotenv(
    dotenv_path="/Users/culiang/Documents/GitHub/ai-engineer-training/week05/.env"
)


# 定义状态 (参考 week05 样式)
class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    research_results: str
    draft: str
    review_comments: str
    final_article: str
    retry_count: int
    current_step: str  # 当前步骤：research, writing, review, polishing
    logs: List[str]


# LLM 工厂 (支持 Gemini 和 Qwen)
def get_llm():
    # 显式读取 .env 获取 model_source
    model_source = os.getenv("model_source", "qwen")

    # 只有当 model_source 为 google 且有 key 时才用 google
    if model_source == "google" and os.getenv("GOOGLE_API_KEY"):
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7,
        )
    else:
        # 复用 week05 配置 (Qwen/DashScope)
        api_key_name = os.getenv("API_KEY_NAME", "DASHSCOPE_API_KEY")
        api_key = os.getenv(api_key_name)

        return ChatOpenAI(
            model=os.getenv("MODEL_NAME", "qwen-turbo"),
            api_key=api_key,
            base_url=os.getenv(
                "BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
            ),
            temperature=0.7,
        )


llm = get_llm()


def get_persona(agent_name: str, retry_count: int) -> str:
    """根据重试次数提升代理等级 (Level 2 Retry)"""
    is_senior = retry_count > 0
    personas = {
        "research": "资深研究分析师" if is_senior else "基础研究员",
        "writing": "资深主编" if is_senior else "内容创作者",
        "review": "首席执行官级审核" if is_senior else "内容审核员",
        "polishing": "文案专家" if is_senior else "文字助理",
    }
    return (
        f"你现在是一名{personas.get(agent_name, '助手')}。你需要以专业的角度完成任务。"
    )


async def research_node(state: State, llm_with_tools):
    """研究节点：调用 MCP 搜集资料"""
    messages = state["messages"]
    persona = get_persona("research", state.get("retry_count", 0))

    # 如果最后一条消息是工具消息，说明搜索已完成，提取结果
    if len(messages) > 0 and messages[-1].type == "tool":
        # 提取所有工具消息的内容作为研究结果，确保转换为字符串
        def message_to_str(msg):
            if isinstance(msg.content, str):
                return msg.content
            if isinstance(msg.content, list):
                return "\n".join(str(item) for item in msg.content)
            return str(msg.content)

        tool_results = [message_to_str(m) for m in messages if m.type == "tool"]
        return {
            "research_results": "\n---\n".join(tool_results),
            "current_step": "research",
            "logs": ["Research: 已完成资料搜集和提取"],
        }

    # 否则，调用 LLM 生成搜索指令
    query = messages[0].content  # 获取最原始的用户需求
    response = await llm_with_tools.ainvoke(
        [
            SystemMessage(
                content=f"{persona} 请针对用户的主题，使用 search_info 工具搜集详尽的资料。"
            ),
            HumanMessage(content=query),
        ]
    )

    return {"messages": [response], "current_step": "research"}


async def writing_node(state: State):
    """撰写节点：基于资料写初稿"""
    research = state.get("research_results", "")
    persona = get_persona("writing", state.get("retry_count", 0))

    prompt = f"请根据以下研究资料撰写文章初稿：\n\n{research}"
    response = await llm.ainvoke(
        [
            SystemMessage(content=f"{persona} 擅长将枯燥的资料转化为引人入胜的文章。"),
            HumanMessage(content=prompt),
        ]
    )

    return {
        "messages": [response],
        "draft": response.content,
        "current_step": "writing",
        "logs": ["Writing: 已生成初稿"],
    }


async def review_node(state: State):
    """审核节点：质量把关"""
    draft = state.get("draft", "")
    persona = get_persona("review", state.get("retry_count", 0))

    # 为了演示重试逻辑，这里可以模拟一些质量问题
    prompt = f"请审核以下文章，检查逻辑和客观性，并给出详细建议。最后请在结尾明确写出 '审核结果：通过' 或 '审核结果：退回重写'。\n\n文章内容：\n{draft}"

    response = await llm.ainvoke(
        [
            SystemMessage(content=f"{persona} 致力于维护极高的内容标准。"),
            HumanMessage(content=prompt),
        ]
    )

    return {
        "messages": [response],
        "review_comments": response.content,
        "current_step": "review",
        "logs": ["Review: 已完成审核并提供建议"],
    }


async def polishing_node(state: State):
    """润色节点：定稿优化"""
    draft = state.get("draft", "")
    comments = state.get("review_comments", "")
    persona = get_persona("polishing", state.get("retry_count", 0))

    prompt = f"初稿：\n{draft}\n\n审核建议：\n{comments}\n\n请参考建议对文章进行最终润色，确保语言流畅优雅，输出最终定稿。"
    response = await llm.ainvoke(
        [
            SystemMessage(content=f"{persona} 擅长文字画龙点睛。"),
            HumanMessage(content=prompt),
        ]
    )

    return {
        "messages": [response],
        "final_article": response.content,
        "current_step": "polishing",
        "logs": ["Polishing: 已输出最终定稿"],
    }
