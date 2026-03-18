import os
import traceback
from typing import List
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.prompts import load_mcp_prompt
import asyncio
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

mcp_client = MultiServerMCPClient(
    {
        "logistics": {
            "url": "http://localhost:8000/mcp",
            "transport": "streamable-http",
        },
        # "weather-map": {
        #     "url": "http://localhost:8001/mcp",
        #     "transport": "streamable-http",
        # },
    },
)

# 状态定义
class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]


def create_llm():
    return ChatTongyi(
        model="qwen-plus",
        temperature=0.1,  # 低温度保证稳定性
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
    )


async def create_chat_llm_with_mcp_tools(mcp_client_session):
    llm = create_llm()
    tools = await load_mcp_tools(mcp_client_session)
    llm_with_tools = llm.bind_tools(tools)

    # 可选：从 MCP 加载 system prompt
    try:
        system_prompt_msg = await load_mcp_prompt(mcp_client_session, "system_prompt")
        system_prompt = system_prompt_msg[0].content
        print("加载到system_prompt:", system_prompt)
    except Exception as e:
        print("未加载到 system prompt，使用默认提示。错误:", e)
        system_prompt = "你是一个智能助手，可以调用工具来回答用户问题。"

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages")
    ])

    return prompt_template | llm_with_tools


async def create_graph(mcp_client_session):
    graph_builder = StateGraph(State)

    #chat-node定义
    chat_llm = await create_chat_llm_with_mcp_tools(mcp_client_session)
    def chat_node(state: State) -> State:
        response = chat_llm.invoke({"messages": state["messages"]})
        return {"messages": [response]}
    graph_builder.add_node("chat", chat_node)
    #tool-node定义
    tools = await load_mcp_tools(mcp_client_session)
    tool_node = ToolNode(tools)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_edge(START, "chat")
    graph_builder.add_conditional_edges("chat", tools_condition, {
        "tools": "tools",
        "__end__": END
    })

    graph_builder.add_edge("tools", "chat")
    
    compiled_graph = graph_builder.compile(checkpointer=MemorySaver())
    
    return compiled_graph

async def main():
    config = {"configurable": {"thread_id": "logistics_thread_001"}}

    async with mcp_client.session("logistics") as logistics_session:

        print("MCP 客户端已连接：Logistics 服务")
        agent = await create_graph(logistics_session)

        print("\n欢迎使用智能物流客服！你可以询问：")
        print("包裹状态、运费、送达时间等")
        print("输入 'quit' 退出\n")

        while True:
            try:
                user_input = input("User: ").strip()
                if user_input.lower() in ["quit", "exit", "退出"]:
                    print("再见！")
                    break

                # 调用代理
                response = await agent.ainvoke(
                    {"messages": [{"role": "user", "content": user_input}]},
                    config=config
                )
                ai_message = response["messages"][-1].content
                print(f"AI: {ai_message}\n")

            except KeyboardInterrupt:
                print("\n已退出。")
                break
            except Exception as e:
                print(f"出错: {e}")
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

#  User: 我的包裹 LGT123456 到哪了？
# AI: 包裹 LGT123456 的当前状态是：已发货，在途中。

# User: 从北京到上海寄一个5公斤的包裹要多少钱？距离大约是1200公里。
# AI: 从北京到上海寄一个5公斤的包裹，距离大约1200公里，运费估算为27.0元。还有其他需要帮忙的吗？

# User: 那大概多久能到？
# AI: 基于距离1200公里的估算，预计送达时间约1天6小时（约34小时）。但实际时效可能受快递公司、起运地/目的地、天气、节假日等因素影响，可能有延迟。

