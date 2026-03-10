"""ReAct Agent工具定义

将现有业务功能封装为工具函数,供Agent调用
"""
from typing import Optional
from langchain_core.tools import tool
from smart_customer_service_extend.utils import get_logger
from smart_customer_service_extend.agents.tools.order_tools import (
    query_order_by_keyword,
    get_order_logistics,
    submit_refund,
    issue_invoice,
)
from smart_customer_service_extend.agents.tools.policy_tools import create_policy_tools
from smart_customer_service_extend.agents.tools.ocr_tools import create_ocr_tools

logger = get_logger(__name__)


def create_customer_service_tools(user_id: str) -> list:
    """创建客服工具列表
    
    Args:
        user_id: 用户ID
        
    Returns:
        工具列表
    """
    
    @tool
    def query_order_tool(keyword: Optional[str] = None, date_str: Optional[str] = None) -> str:
        """查询用户订单。输入: keyword(可选), date_str(可选,如'昨天'/'今天')。"""
        try:
            return query_order_by_keyword.invoke(
                {"user_id": user_id, "keyword": keyword, "date_str": date_str}
            )
        except Exception as e:
            logger.error(f"[Tool Error] query_order_by_keyword: {e}", exc_info=True)
            return f"查询订单失败: {str(e)}"

    # 返回工具列表
    tools = [
        query_order_tool,
        get_order_logistics,
        submit_refund,
        issue_invoice,
        *create_policy_tools(),
        *create_ocr_tools(),
    ]
    
    logger.debug(f"创建了 {len(tools)} 个工具: {[t.name for t in tools]}")
    
    return tools
