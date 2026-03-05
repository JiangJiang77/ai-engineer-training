"""LangGraph工作流条件边逻辑

定义工作流的路由逻辑
"""
from smart_customer_service.workflow.state import CustomerServiceState, Intent, NodeName
from smart_customer_service.utils import get_logger

logger = get_logger(__name__)


def route_by_intent(state: CustomerServiceState) -> str:
    """根据意图路由到不同的业务节点
    
    Returns:
        下一个节点名称
    """
    intent = state.get("intent")
    
    logger.debug(f"路由决策: 意图={intent}")

    # 未知意图默认走通用回复
    return Intent.route_for(intent)


def should_continue(state: CustomerServiceState) -> str:
    """判断是否继续处理
    
    Returns:
        下一个节点名称或END
    """
    next_action = state.get("next_action")
    
    if next_action == "end":
        return NodeName.END
    else:
        return NodeName.CONTEXT_MANAGEMENT
