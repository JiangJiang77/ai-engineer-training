"""LangGraph工作流图定义

构建客服系统的工作流图
"""
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from smart_customer_service_extend.workflow.state import CustomerServiceState, NodeName
from smart_customer_service_extend.workflow.nodes import (
    input_preprocessing_node,
    intent_recognition_node,
    context_management_node,
    logistics_query_node,
    refund_processing_node,
    invoice_processing_node,
    policy_retrieval_node,
    llm_response_node
)
from smart_customer_service_extend.workflow.edges import route_by_intent
from smart_customer_service_extend.utils import get_logger

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
    workflow.add_node(NodeName.INPUT_PREPROCESSING, input_preprocessing_node)
    workflow.add_node(NodeName.INTENT_RECOGNITION, intent_recognition_node)
    workflow.add_node(NodeName.CONTEXT_MANAGEMENT, context_management_node)
    workflow.add_node(NodeName.LOGISTICS_QUERY, logistics_query_node)
    workflow.add_node(NodeName.REFUND_PROCESSING, refund_processing_node)
    workflow.add_node(NodeName.INVOICE_PROCESSING, invoice_processing_node)
    workflow.add_node(NodeName.POLICY_RETRIEVAL, policy_retrieval_node)
    workflow.add_node(NodeName.LLM_RESPONSE, llm_response_node)
    
    # 设置入口点
    workflow.set_entry_point(NodeName.INPUT_PREPROCESSING)
    
    # 添加边
    # 输入预处理 -> 意图识别
    workflow.add_edge(NodeName.INPUT_PREPROCESSING, NodeName.INTENT_RECOGNITION)
    
    # 意图识别 -> 上下文管理
    workflow.add_edge(NodeName.INTENT_RECOGNITION, NodeName.CONTEXT_MANAGEMENT)
    
    # 上下文管理 -> 根据意图路由
    workflow.add_conditional_edges(
        NodeName.CONTEXT_MANAGEMENT,
        route_by_intent,
        {
            NodeName.LOGISTICS_QUERY: NodeName.LOGISTICS_QUERY,
            NodeName.REFUND_PROCESSING: NodeName.REFUND_PROCESSING,
            NodeName.INVOICE_PROCESSING: NodeName.INVOICE_PROCESSING,
            NodeName.POLICY_RETRIEVAL: NodeName.POLICY_RETRIEVAL,
            NodeName.LLM_RESPONSE: NodeName.LLM_RESPONSE
        }
    )
    
    # 所有业务节点 -> END
    workflow.add_edge(NodeName.LOGISTICS_QUERY, END)
    workflow.add_edge(NodeName.REFUND_PROCESSING, END)
    workflow.add_edge(NodeName.INVOICE_PROCESSING, END)
    workflow.add_edge(NodeName.POLICY_RETRIEVAL, END)
    workflow.add_edge(NodeName.LLM_RESPONSE, END)
    
    # 编译图
    if checkpointer is None:
        raise ValueError(
            "必须提供 checkpointer 参数以启用持久化存储。"
            "请使用 SqliteSaver.from_conn_string() 创建 checkpointer。"
        )
        
    app = workflow.compile(checkpointer=checkpointer)
    
    logger.debug("工作流图创建成功")
    
    return app


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


# 导出
__all__ = ["create_workflow_graph", "run_workflow", "print_workflow_graph"]


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
