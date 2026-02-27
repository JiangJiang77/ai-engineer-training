from enum import Enum
import json
import redis
import os
from typing import Annotated, Sequence, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI


class MessageType(Enum):
    HUMAN = "human"
    AI = "ai"

llm = ChatOpenAI(model="qwen-turbo", temperature=0.3,
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

class GraphState(TypedDict):
    messages: Annotated[Sequence, add_messages]


class LongTermMemory:
    def __init__(self, thread_id: str, redis_client_url: str="redis://localhost:10079/0"):
        self.thread_id = thread_id
        self.memory_key = f"memory:{thread_id}"

        try:
            self.redis_client = redis.from_url(redis_client_url)
            # 建立连接
            self.redis_client.ping()
            print("Redis connected successfully")
        except Exception as e:
            print(f"Error connecting to Redis: {e}, url:{redis_client_url}")
            self.redis_client = None

    def save_memory(self, memory_type, content):
        if self.redis_client is None:
            return

        message_to_save = {
            "type": memory_type,
            "content": content
        }
        try:
            self.redis_client.lpush(self.memory_key, json.dumps(message_to_save))
        except Exception as e:
            print(f"Error saving memory to Redis, key: {self.memory_key}, error: {e}")
            

    def get_memory(self, limit):
        if self.redis_client is None:
            return []
        
        try:
            his_messages = self.redis_client.lrange(self.memory_key, 0, limit)
            messages = []
            for msg_json in reversed(his_messages):
                try:
                    msg = json.loads(msg_json)
                    if msg["type"] == MessageType.HUMAN.value:
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["type"] == MessageType.AI.value:
                        messages.append(AIMessage(content=msg["content"]))
                    else:
                        print(f"Unknown message type: {msg['type']}, msg: {msg}")
                except Exception as e:
                    print(f"Error parsing message: {e}, msg: {msg_json}")
            return messages
        except Exception as e:
            print(f"Error getting memory from Redis: {e}")
            return []

    def clear_memory(self):
        if self.redis_client is None:
            return
        self.redis_client.delete(self.memory_key)



def chat_node(state: GraphState, config: RunnableConfig):
    """
    处理聊天信息
    """
    # 1. 从 config 中获取 thread_id
    thread_id = config["configurable"].get("thread_id", "default")
    # 2. 提取用户消息
    last_message = state["messages"][-1]

    # 初始化长期记忆
    memory = LongTermMemory(thread_id=thread_id)
    if isinstance(last_message, HumanMessage):
        memory.save_memory(MessageType.HUMAN.value, last_message.content)
    
    history_message = memory.get_memory(limit=10)

    if history_message:
        all_messages = history_message + [last_message]
    else:
        all_messages = [last_message]
    
    print(f"使用 {len(all_messages)} 条消息作为上下文")

    # 3. 构建消息列表，包含 SystemMessage
    system_msg = SystemMessage(content="你是一个友好的聊天助手，请根据上下文回答用户的问题")
    full_messages = [system_msg] + all_messages
    
    ai_response = llm.invoke(full_messages)
    print(f"llm回复: {ai_response.content}")
    memory.save_memory(MessageType.AI.value, ai_response.content)
    return {"messages": [ai_response]}
    
    
graph_builder = StateGraph(GraphState)
graph_builder.add_node("chat_node", chat_node)
graph_builder.add_edge(START, "chat_node")
graph_builder.add_edge("chat_node", END)

graph = graph_builder.compile(checkpointer=MemorySaver())

def print_memory(thread_id: str):
    memory = LongTermMemory(thread_id=thread_id)
    messages = memory.get_memory(limit=10)
    print(f"\n=== 会话 '{thread_id}' 的记忆 ===")
    if not messages:
        print("无记录")
    else:
        for i, msg in enumerate(messages, 1):
            role = "用户" if isinstance(msg, HumanMessage) else "助手"
            print(f"{role}: {msg.content}")

def delete_memory(thread_id: str):
    memory = LongTermMemory(thread_id=thread_id)
    memory.clear_memory()
    print(f"已删除会话 '{thread_id}' 的记忆")
    
def test_long_memory():

    # 清除 Alice 的记忆
    delete_memory("alice")
    print_memory("alice")
    delete_memory("bob")
    print_memory("bob")

    # Alice 环节
    print("\n--- Alice 开始对话 ---")
    thread_id = "alice"
    graph.invoke({"messages": [HumanMessage(content="你好，我叫Alice")]}, config={"configurable": {"thread_id": thread_id}})
    graph.invoke({"messages": [HumanMessage(content="我喜欢游泳")]}, config={"configurable": {"thread_id": thread_id}})
    graph.invoke({"messages": [HumanMessage(content="我今年18岁")]}, config={"configurable": {"thread_id": thread_id}})
    graph.invoke({"messages": [HumanMessage(content="我叫什么名字？")]}, config={"configurable": {"thread_id": thread_id}})
    
    # Bob 环节
    print("\n--- Bob 开始对话 ---")
    graph.invoke({"messages": [HumanMessage(content="你好，我叫Bob")]}, config={"configurable": {"thread_id": "bob"}})
    graph.invoke({"messages": [HumanMessage(content="我喜欢打篮球")]}, config={"configurable": {"thread_id": "bob"}})
    graph.invoke({"messages": [HumanMessage(content="我今年22岁")]}, config={"configurable": {"thread_id": "bob"}})
    graph.invoke({"messages": [HumanMessage(content="我叫什么名字？")]}, config={"configurable": {"thread_id": "bob"}})
    
    # 验证
    print_memory("alice")
    print_memory("bob")
    
    # 清除 Alice 的记忆
    delete_memory("alice")
    print_memory("alice")

    print("\n--- Alice 再次对话 ---")
    thread_id = "alice"
    graph.invoke({"messages": [HumanMessage(content="我叫什么名字？")]}, config={"configurable": {"thread_id": thread_id}})

    

if __name__ == "__main__":
    test_long_memory()
    