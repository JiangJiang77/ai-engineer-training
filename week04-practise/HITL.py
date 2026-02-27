
from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END, add_messages
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

# 状态定义 金额和是否退款（需要流转的信息）

class RefundState(TypedDict):
    messages: Annotated[Sequence, add_messages]
    amount: int
    needs_approval: bool
    is_approved: bool

# 解析退款金额
def extract_amount(state: RefundState):
    """
    解析请求：从用户输入中提取退款金额。
    """
    # 获取最后一条历史消息
    last_message = state["messages"][-1].content.strip()
    
    try:
        amount = int(last_message)
    except:
        amount = 0
    
    return {
        "amount": amount,
        "needs_approval": False,
        "is_approved": False
        }

# 退款金额初审
def ai_review(state: RefundState):
    """
    AI 初审：金额 ≤ 500元：自动批准。金额 > 500元：标记为“需人工审核”。
    """

    amount = state["amount"]

    if amount <=0:
        reply = "退款金额无效"
        needs_approval=False
    elif amount > 500:
        reply = "退款金额过大，需要人工审核"
        needs_approval=True
    else:
        reply = "退款金额自动批准"
        needs_approval=False
    
    return {
        "messages": [AIMessage(content=reply)],
        "needs_approval": needs_approval
        }

def human_approval(state: RefundState):
    """
    人工干预：若需审核，系统暂停并使用 input() 等待用户手动输入“是/否”。
    """
    amount = state["amount"]
    
    print(f"退款金额为：{amount}元,等待人工审核")
    
    while True:
        decision = input("是否批准退款？(是/否)") 
        if decision in ["是", "否","y","n"]:
            break
        else:
            print("输入无效，请输入是 或 否")

    approved = decision in ["是", "y"]
    reply = "批准" if approved else "拒绝"
    print(f"人工审核结果：{reply}")
    
    return {
        "messages": [HumanMessage(content=reply)],
        "is_approved": approved
    }

def handle_refund(state: RefundState):
    """
    处理退款：汇总自动或人工的决策，给出最终反馈。
    只处理腿
    """
    amount = state["amount"]
    needs_approval = state["needs_approval"]
    is_approved = state["is_approved"]

    if not needs_approval:
        reply = "退款已自动处理"
    elif is_approved:
        reply = "退款已批准并处理"
    elif not is_approved:
        reply = "退款已拒绝"
    else:
        reply = "退款处理失败,状态未知"
    
    return {
        "messages": [AIMessage(content=reply)],
    }    

def should_get_approval_router(state: RefundState):
    """
    判断是否需要人工审核。
    """
    return "human_approval" if state["needs_approval"] else "handle_refund"

def print_messages(messages):
    """
    友好地打印消息列表
    """
    print("\n--- 对话历史 ---")
    for i, msg in enumerate(messages):
        # 获取类名，如 HumanMessage, AIMessage
        msg_type = type(msg).__name__
        print(f"{i+1}. [{msg_type}]: {msg.content}")
    print("----------------\n")


state_graph = StateGraph(RefundState)

state_graph.add_node("extract_amount", extract_amount)
state_graph.add_node("ai_review", ai_review)
state_graph.add_node("should_get_approval_router", should_get_approval_router)
state_graph.add_node("human_approval", human_approval)
state_graph.add_node("handle_refund", handle_refund)


state_graph.add_edge(START, "extract_amount")
state_graph.add_edge("extract_amount", "ai_review")
state_graph.add_conditional_edges("ai_review", should_get_approval_router)
state_graph.add_edge("human_approval", "handle_refund")
state_graph.add_edge("handle_refund", END)

# 编译图
checkpointer = MemorySaver()
app = state_graph.compile(checkpointer=checkpointer)

def process_refund_request(amount: str, thread_id: str = "default"):
    """
    处理退款申请完整流程
    """
    print(f"\n 开始处理退款申请...")
    print("="*50)

    config = {"configurable": {"thread_id": thread_id}}

    result = app.invoke({
        "messages": [HumanMessage(content=amount)]
    }, config=config)

    print_messages(result["messages"])
    print("="*50)
    print(" 退款流程完成")
    
    return result

def demo():
    # 场景1：小额退款（自动处理）
    print("\n 场景1：小额退款（300元）- 自动处理")
    process_refund_request("300", "user1")
    
    print("\n" + "="*60)
    
    # 场景2：大额退款（需要人工审批）
    print("\n 场景2：大额退款（800元）- 需要人工审批")
    print(" 这里会真正暂停等待你的输入！")
    process_refund_request("800", "user2")

    # 场景3：无效金额
    print("\n 场景3：无效金额")
    process_refund_request("0", "user3")


if __name__ == "__main__":
    demo()   