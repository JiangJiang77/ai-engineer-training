"""LangGraph 对话持久化演示

展示如何通过 thread_id 实现对话记忆，且无需修改原有代码逻辑。
"""
from langchain_core.messages import HumanMessage
from smart_customer_service.workflow.persistent_graph import create_persistent_workflow_graph
from smart_customer_service.database import authenticate_user

def run_persistent_demo():
    print("\n" + "=" * 60)
    print("🤖 LangGraph 对话持久化演示 (非侵入式)")
    print("=" * 60)
    
    # 1. 初始化持久化图
    app = create_persistent_workflow_graph()
    
    # 2. 模拟登录
    user = authenticate_user("test_user", "password123")
    user_id = user["user_id"]
    
    # 3. 定义会话配置 (thread_id 是关键)
    config = {"configurable": {"thread_id": "demo_session_123"}}
    
    # --- 第一轮对话 ---
    print("\n[第一轮对话]")
    user_input_1 = "你好，我是粗粮。我昨天下了一个笔记本电脑的订单。"
    print(f"用户: {user_input_1}")
    
    state_1 = {
        "user_id": user_id,
        "session_id": "demo_session_123",
        "messages": [HumanMessage(content=user_input_1)],
        "user_input": user_input_1,
    }
    
    result_1 = app.invoke(state_1, config=config)
    print(f"客服: {result_1.get('response')}")
    
    # --- 第二轮对话 (利用记忆) ---
    print("\n" + "-" * 40)
    print("[第二轮对话 - 验证记忆]")
    user_input_2 = "我刚才说我叫什么名字？我买的是什么？"
    print(f"用户: {user_input_2}")
    
    # 注意：我们只需传入新的输入，之前的 messages 会由 LangGraph 自动维护（或手动拼接）
    # 在这个工作流中，llm_response_node 会查阅历史 messages
    state_2 = {
        "user_id": user_id,
        "session_id": "demo_session_123",
        "messages": [HumanMessage(content=user_input_2)],
        "user_input": user_input_2,
    }
    
    result_2 = app.invoke(state_2, config=config)
    print(f"客服: {result_2.get('response')}")
    
    print("\n" + "=" * 60)
    print("✅ 持久化演示完成!")
    print("=" * 60)

if __name__ == "__main__":
    run_persistent_demo()
