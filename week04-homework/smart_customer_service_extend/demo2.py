"""
阶段二多轮对话和工具调用
LangGraph工作流图定义
"""
import argparse
import uuid
from typing import List

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from smart_customer_service_extend.workflow.state import CustomerServiceState, NodeName
from smart_customer_service_extend.workflow.nodes import (
    input_preprocessing_node,
    intent_recognition_node,
    context_management_node,
    agent_tool_call_node,
    llm_response_node
)
from smart_customer_service_extend.utils import get_logger
from smart_customer_service_extend.repository.session_repo import get_user_by_username

logger = get_logger(__name__)


def create_workflow_graph(checkpointer=None):
    """创建工作流图

    Args:
        checkpointer: 检查点保存器 (可选)

    Returns:
        编译后的工作流图
    """
    # 创建状态图
    workflow = StateGraph(CustomerServiceState)

    # 添加节点
    # 输入预处理
    workflow.add_node(NodeName.INPUT_PREPROCESSING, input_preprocessing_node)
    # 意图识别
    workflow.add_node(NodeName.INTENT_RECOGNITION, intent_recognition_node)
    # 上下文管理
    workflow.add_node(NodeName.CONTEXT_MANAGEMENT, context_management_node)
    # 
    workflow.add_node(NodeName.AGENT_TOOL_CALL, agent_tool_call_node)
    # LLM生成回复
    workflow.add_node(NodeName.LLM_RESPONSE, llm_response_node)

    # 设置入口点
    workflow.set_entry_point(NodeName.INPUT_PREPROCESSING)

    # 添加边
    # 输入预处理 -> 意图识别
    workflow.add_edge(NodeName.INPUT_PREPROCESSING, NodeName.INTENT_RECOGNITION)
    # 意图识别 -> 上下文管理
    workflow.add_edge(NodeName.INTENT_RECOGNITION, NodeName.CONTEXT_MANAGEMENT)
    # 上下文管理 -> 工具调用
    workflow.add_conditional_edges(NodeName.CONTEXT_MANAGEMENT, route_agent_tool_call)
    # 生成客服回复
    workflow.add_edge(NodeName.LLM_RESPONSE, END)

    # 编译图
    if checkpointer is None:
        raise ValueError(
            "必须提供 checkpointer 参数以启用持久化存储。"
            "请使用 SqliteSaver.from_conn_string() 创建 checkpointer。"
        )

    compiled_graph = workflow.compile(checkpointer=checkpointer)

    logger.debug("工作流图创建成功")

    return compiled_graph

def route_agent_tool_call(state: CustomerServiceState):
    """条件路由：业务意图走 Agent 工具调用，其余走通用回复。"""
    intent = state.get("intent")
    if intent in {
        "orders_query",
        "logistics_query",
        "refund_application",
        "invoice_issuance",
        "policy_query",
        "agent_tool_call",
    }:
        return NodeName.AGENT_TOOL_CALL
    return NodeName.LLM_RESPONSE


def run_workflow(user_id: str, session_id: str, user_input: str):
    """运行工作流

    Args:
        user_id: 用户ID
        session_id: 会话ID
        user_input: 用户输入

    Returns:
        系统回复
    """
    logger.debug(f"运行工作流: user_id={user_id}, session_id={session_id}, input={user_input}")

    # 初始化状态
    initial_state = {
        "user_id": user_id,
        "session_id": session_id,
        "messages": [HumanMessage(content=user_input)],
        "user_input": user_input,
        "intent": None,
        "context": {},
        "order_info": None,
        "retrieved_docs": None,
        "next_action": None,
        "response": None,
        "need_more_info": False
    }

    # 执行工作流
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        db_path = "data/checkpoints.db"
        with SqliteSaver.from_conn_string(db_path) as checkpointer:
            # 创建工作流
            app = create_workflow_graph(checkpointer)

            # 使用会话ID作为thread_id
            config = {"configurable": {"thread_id": session_id}}
            result = app.invoke(initial_state, config=config)

            response = result.get("response", "抱歉,我无法处理您的请求。")
            logger.debug(f"工作流执行成功: response={response[:100]}...")
            return response

    except Exception as e:
        logger.error(f"工作流执行失败: {e}", exc_info=True)
        return f"抱歉,处理您的请求时出错: {str(e)}"


def call_workflow(user_input: str) -> str:
    """以最简入参调用工作流。"""
    text = (user_input or "").strip()
    if not text:
        return "输入为空，无法处理。"

    return run_workflow(
        user_id="u1001",
        session_id=f"demo2-call-{uuid.uuid4().hex[:8]}",
        user_input=text,
    )




# 导出
__all__ = ["create_workflow_graph", "run_workflow", "call_workflow", "print_workflow_graph"]


def print_workflow_graph(app):
    """打印工作流图流程图(Mermaid格式)并保存为图片"""
    import os
    print("\n" + "-" * 20 + " 工作流流程图 (Mermaid) " + "-" * 20)
    try:
        # 获取mermaid源码
        mermaid_code = app.get_graph().draw_mermaid()
        print(mermaid_code)

        # 保存为图片
        try:
            # 确保media目录存在
            media_dir = "media"
            if not os.path.exists(media_dir):
                os.makedirs(media_dir)

            # 使用 draw_mermaid_png 获取图片字节流
            png_data = app.get_graph().draw_mermaid_png()
            file_path = os.path.join(media_dir, "workflow.png")

            with open(file_path, "wb") as f:
                f.write(png_data)
            print(f"\n[提示] 流程图已保存至: {file_path}")
        except Exception as img_e:
            # 可能是因为缺少 pygraphviz 或相关依赖, 静默失败或打印提示
            print(f"\n[提示] 自动保存图片失败 (可能缺少依赖): {img_e}")

    except Exception as e:
        print(f"无法生成流程图: {e}")
    print("-" * 60 + "\n")


if __name__ == "__main__":
    session_id = "session_id_1"
    user_name = "test_user"

    user = get_user_by_username(user_name)
    user_id = user['user_id']

    user_inputs = [
        "我要查昨天的订单",
        "手表发货了吗",
        "我要查电脑的订单信息",
        "我要开电脑的发票，订单号是97631813-52ee-464f-afd9-706a9dd42589",
        "media/5561770796260_.pic.jpg",
        "media/2026021103594534377439.mp3"
    ]

    for user_input in user_inputs:
        print(f"\n==================START========================")
        print(f"\n用户：{user_input}")

        response = run_workflow(user_id=user_id, session_id=session_id, user_input=user_input)
        print(f"客服：{response}")
        print(f"\n==================END========================")
