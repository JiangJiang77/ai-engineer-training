import os
from typing import Annotated  # 用于为函数参数添加类型注解

from langchain_core.messages import convert_to_messages  # 将消息列表转换为标准格式
from langchain_core.tools import tool, InjectedToolCallId  # 定义工具函数和注入工具调用ID
from langchain_community.chat_models import ChatTongyi
from langchain.agents import create_agent

from langgraph.prebuilt import InjectedState  # 注入状态
from langgraph.graph import StateGraph, START, MessagesState  # 构建状态图，定义起始节点，消息状态类型
from langgraph.types import Command  # 用于控制流程跳转的命令


# ------------------- 定义基础功能工具 -------------------
## 定义预定酒店工具函数
def book_hotel(hotel_name: str) -> str:
    """模拟预订酒店的操作"""
    # print(f"已成功预订 {hotel_name} 的住宿。")
    return f"已成功预订 {hotel_name} 的住宿。"

## 定于预定机票实现函数
def book_flight(from_airport: str, to_airport: str) -> str:
    """模拟预订航班的操作"""
    # print(f"已成功预订从 {from_airport} 到 {to_airport} 的航班。")
    return f"已成功预订从 {from_airport} 到 {to_airport} 的航班。"

# ------------------- 创建移交工具 -------------------
## 定义移交工具工厂类
def create_handoff_tool(*,agent_name:str,agent_description:str | None = None):
    """
        移交 Tool工厂函数：创建可以将控制权移交到指定代理的工具
        这是实现多代理协作的核心机制
    """
    name = f"handoff_to_{agent_name}"
    description = agent_description or f"移交到 {agent_name} 的工具"

    @tool(name, description=description)
    def handoff_tool(
        state: Annotated[MessagesState, InjectedState], # 注入当前对话状态
        tool_call_id: Annotated [str,InjectedToolCallId], # 注入本次工具调用的ID
    ) -> Command:
        """移交到 {agent_name} 的工具"""
        # print(f"已成功移交到 {agent_name} 的工具,tool_call_id: {tool_call_id}")
        tool_message ={
            "role": "tool",
            "content": f"移交到 {agent_name} 的工具",
            "tool_call_id": tool_call_id,
        }
        return Command(
            goto=agent_name,
            update={"messages": state["messages"] + [tool_message]},
            graph=Command.PARENT
        )
    return handoff_tool

# 定义移交hotel_assistant 移交到 flight_assistant 的工具
handoff_to_flight_assistant = create_handoff_tool(
    agent_name="flight_assistant",agent_description="当前任务执行完成后，转接给航线预定助手")
# 定义移交flight_assistant 移交到 hotel_assistant 的工具
handoff_to_hotel_assistant = create_handoff_tool(
    agent_name="hotel_assistant",agent_description="当前任务执行完成后，转接给酒店预定助手")

# ------------------- 定义langgraph agent node节点 -------------------
## 定义langgraph node节点
# 创建 hotel_assistant，选择模型,绑定tool （预定酒店工具函数、转交 tool函数），定义提示词 
# 初始化LLM
llm = ChatTongyi(
    model="qwen-plus",
    temperature=0.1,  # 低温度保证稳定性
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
)
hotel_assistant = create_agent(
    model=llm,
    tools=[book_hotel, handoff_to_flight_assistant],
    system_prompt="""
    你是一名酒店预定助手，请根据用户的需求，优先预订好酒店。
    如果用户还需要预订机票，请转接给航线助理。
    """,
    name="hotel_assistant"
)

# 创建 flight_assistant，选择模型,绑定tool （预定机票工具函数、转交 tool函数），定义提示词 
flight_assistant = create_agent(
    model=llm,
    tools=[book_flight, handoff_to_hotel_assistant],
    system_prompt="""
    你是一名航线预定助手，请根据用户的需求，优先预订好机票。
    如果用户还需要预订酒店，请转接给酒店助理。
    """,
    name="flight_assistant"
)
# 定义langgraph workflow ，编译

multi_agent_workflow = (
    StateGraph(MessagesState)
    .add_node("hotel_assistant", hotel_assistant)
    .add_node("flight_assistant", flight_assistant)
    .add_edge(START, "flight_assistant")
    .compile())

# 编译好的 graph 进行执行


def main():

    for chunk in multi_agent_workflow.stream({
            "messages": [
                {"role": "user", "content": "我想预订从北京到上海的机票，以及上海迪斯尼乐园酒店的住宿"}
            ]
        }, 
        stream_mode="values", subgraphs=True):
        # subgraphs=True 时返回 (namespace, data) 元组；否则直接返回 data 字典
        data = chunk[1] if isinstance(chunk, tuple) else chunk
        if "messages" in data and data["messages"]:
            print(convert_to_messages(data["messages"])[-1].content)


if __name__ == "__main__":
    main()





    
