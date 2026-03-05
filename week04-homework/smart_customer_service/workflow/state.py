"""LangGraph工作流状态定义

定义客服系统的状态结构
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph.message import add_messages


class CustomerServiceState(TypedDict):
    """客服系统状态
    
    状态字段说明:
    - user_id: 用户ID
    - session_id: 会话ID
    - messages: 对话消息列表(使用add_messages自动管理)
    - user_input: 当前用户输入
    - intent: 识别的用户意图
    - context: 对话上下文信息(时间、订单号、关键字等)
    - order_info: 查询到的订单信息
    - retrieved_docs: 检索到的文档内容
    - next_action: 下一步操作
    - response: 系统回复
    - need_more_info: 是否需要追问更多信息
    """
    user_id: str
    session_id: str
    messages: Annotated[List[BaseMessage], add_messages]
    user_input: str
    intent: Optional[str]
    context: Dict[str, Any]
    order_info: Optional[Dict[str, Any]]
    retrieved_docs: Optional[str]
    next_action: Optional[str]
    response: Optional[str]
    need_more_info: bool


# 节点名称常量
class NodeName:
    """节点名称常量"""
    INPUT_PREPROCESSING = "input_preprocessing"
    INTENT_RECOGNITION = "intent_recognition"
    CONTEXT_MANAGEMENT = "context_management"
    LOGISTICS_QUERY = "logistics_query"
    REFUND_PROCESSING = "refund_processing"
    INVOICE_PROCESSING = "invoice_processing"
    POLICY_RETRIEVAL = "policy_retrieval"
    LLM_RESPONSE = "llm_response"
    END = "end"


# 意图常量与元数据
class Intent:
    """意图类型常量（含code/name/desc/route元数据）"""

    LOGISTICS_QUERY = "logistics_query"
    REFUND_APPLICATION = "refund_application"
    INVOICE_ISSUANCE = "invoice_issuance"
    POLICY_QUERY = "policy_query"
    GENERAL_CHAT = "general_chat"
    UNKNOWN = "unknown"

    META = {
        LOGISTICS_QUERY: {
            "name": "物流查询",
            "desc": "查询订单物流、发货状态、订单列表",
            "route": NodeName.LOGISTICS_QUERY,
        },
        REFUND_APPLICATION: {
            "name": "退款申请",
            "desc": "申请退款、退货、售后退款处理",
            "route": NodeName.REFUND_PROCESSING,
        },
        INVOICE_ISSUANCE: {
            "name": "发票开具",
            "desc": "开票、发票信息处理",
            "route": NodeName.INVOICE_PROCESSING,
        },
        POLICY_QUERY: {
            "name": "政策查询",
            "desc": "查询售后、物流、支付、质保等政策",
            "route": NodeName.POLICY_RETRIEVAL,
        },
        GENERAL_CHAT: {
            "name": "一般对话",
            "desc": "问候、感谢、闲聊等非业务请求",
            "route": NodeName.LLM_RESPONSE,
        },
        UNKNOWN: {
            "name": "未知意图",
            "desc": "无法准确识别意图，降级到通用回复",
            "route": NodeName.LLM_RESPONSE,
        },
    }

    @classmethod
    def codes(cls) -> list[str]:
        return list(cls.META.keys())

    @classmethod
    def route_for(cls, intent_code: Optional[str]) -> str:
        meta = cls.META.get(intent_code or cls.UNKNOWN, cls.META[cls.UNKNOWN])
        return str(meta["route"])
