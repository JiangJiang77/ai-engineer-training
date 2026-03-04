"""ReAct Agent工具定义

将现有业务功能封装为工具函数,供Agent调用
"""
from langchain_core.tools import tool
from smart_customer_service.utils import get_logger
from smart_customer_service.agents.tools.order_tools import create_order_tools
from smart_customer_service.agents.tools.policy_tools import create_policy_tools
from smart_customer_service.agents.tools.ocr_tools import create_ocr_tools

logger = get_logger(__name__)


def create_customer_service_tools(user_id: str) -> list:
    """创建客服工具列表
    
    Args:
        user_id: 用户ID
        
    Returns:
        工具列表
    """
    
    # 返回工具列表
    tools = [
        *create_order_tools(user_id),
        *create_policy_tools(),
        *create_ocr_tools(),
    ]
    
    logger.debug(f"创建了 {len(tools)} 个工具: {[t.name for t in tools]}")
    
    return tools
