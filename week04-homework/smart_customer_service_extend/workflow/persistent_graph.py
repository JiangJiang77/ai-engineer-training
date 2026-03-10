"""LangGraph 持久化工作流图封装

在不修改原有 graph.py 的前提下，通过外部包装实现对话持久化。
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

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


def create_persistent_workflow_graph():
    """创建带有持久化能力的封装工作流图
    
    Returns:
        编译后且带有 checkpointer 的工作流图
    """
    # 创建状态图
    workflow = StateGraph(CustomerServiceState)
    
    # 添加节点 (复用原有的节点函数)
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
    workflow.add_edge(NodeName.INPUT_PREPROCESSING, NodeName.INTENT_RECOGNITION)
    workflow.add_edge(NodeName.INTENT_RECOGNITION, NodeName.CONTEXT_MANAGEMENT)
    
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
    
    workflow.add_edge(NodeName.LOGISTICS_QUERY, END)
    workflow.add_edge(NodeName.REFUND_PROCESSING, END)
    workflow.add_edge(NodeName.INVOICE_PROCESSING, END)
    workflow.add_edge(NodeName.POLICY_RETRIEVAL, END)
    workflow.add_edge(NodeName.LLM_RESPONSE, END)
    
    # 定义内存 Checkpointer
    # 注意：在生产环境中可以使用 SqliteSaver 实现跨进程持久化
    checkpointer = MemorySaver()
    
    # 编译图并添加 checkpointer
    app = workflow.compile(checkpointer=checkpointer)
    
    logger.debug("持久化工作流图创建成功 (使用 MemorySaver)")
    
    return app
