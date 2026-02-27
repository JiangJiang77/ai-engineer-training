"""订单相关工具

提供订单查询、退款、发票等功能
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain.tools import tool

from smart_customer_service.database import query_orders, update_order_status
from smart_customer_service.utils import parse_relative_time, get_logger

logger = get_logger(__name__)

@tool
def query_order_by_keyword(user_id: str, keyword: str, date_str: Optional[str] = None) -> str:
    """根据关键字和日期查询订单
    
    Args:
        user_id: 用户ID
        keyword: 订单名称关键字
        date_str: 日期字符串,如"昨天"、"今天"
    
    Returns:
        查询结果的JSON字符串
    """
    try:
        filters = {"keyword": keyword}
        
        # 解析日期
        if date_str:
            order_date = parse_relative_time(date_str)
            filters["order_date"] = order_date.date()
        
        orders = query_orders(user_id, **filters)
        
        if not orders:
            return f"未找到包含'{keyword}'的订单"
        
        # 格式化结果(orders已经是字典列表)
        for order in orders:
            order["order_date"] = order["order_date"].strftime("%Y-%m-%d")
        
        return str(orders)
    except Exception as e:
        logger.error(f"查询订单失败: {e}")
        return f"查询订单时出错: {str(e)}"


@tool
def query_orders_by_date(user_id: str, date_str: str) -> str:
    """根据日期查询订单列表
    
    Args:
        user_id: 用户ID
        date_str: 日期字符串,如"昨天"、"今天"
    
    Returns:
        订单列表的JSON字符串
    """
    try:
        # 解析日期
        order_date = parse_relative_time(date_str)
        
        orders = query_orders(user_id, order_date=order_date.date())
        
        if not orders:
            return f"{date_str}没有订单"
        
        # 格式化结果(orders已经是字典列表)
        for order in orders:
            order["order_date"] = order["order_date"].strftime("%Y-%m-%d")
        
        return str(orders)
    except Exception as e:
        logger.error(f"查询订单失败: {e}")
        return f"查询订单时出错: {str(e)}"


@tool
def get_order_logistics(order_id: str) -> str:
    """获取订单物流状态
    
    Args:
        order_id: 订单ID
    
    Returns:
        物流状态信息
    """
    try:
        from smart_customer_service.database.crud import get_db_session
        from smart_customer_service.database.models import Order
        
        with get_db_session() as session:
            order = session.query(Order).filter(Order.order_id == order_id).first()
            
            if not order:
                return f"未找到订单 {order_id}"
            
            return f"订单【{order.order_name}】物流状态: {order.logistics_status}"
    except Exception as e:
        logger.error(f"获取物流状态失败: {e}")
        return f"获取物流状态时出错: {str(e)}"


@tool
def query_refundable_orders(user_id: str) -> str:
    """查询可退款订单
    
    Args:
        user_id: 用户ID
    
    Returns:
        可退款订单列表
    """
    try:
        orders = query_orders(user_id, can_refund=1)
        
        if not orders:
            return "没有可退款的订单"
        
        # 格式化结果(orders已经是字典列表)
        for order in orders:
            order["order_date"] = order["order_date"].strftime("%Y-%m-%d")
        
        return str(orders)
    except Exception as e:
        logger.error(f"查询可退款订单失败: {e}")
        return f"查询可退款订单时出错: {str(e)}"


@tool
def submit_refund(order_id: str) -> str:
    """提交退款申请
    
    Args:
        order_id: 订单ID
    
    Returns:
        退款处理结果
    """
    try:
        order = update_order_status(order_id, "refunding")
        
        if not order:
            return f"未找到订单 {order_id}"
        
        return f"订单【{order.order_name}】退款申请已提交,预计3-5个工作日退款到账"
    except Exception as e:
        logger.error(f"提交退款失败: {e}")
        return f"提交退款时出错: {str(e)}"


@tool
def query_invoiceable_orders(user_id: str, keyword: Optional[str] = None) -> str:
    """查询可开票订单
    
    业务规则:只有已签收(delivered)的订单才能开具发票
    
    Args:
        user_id: 用户ID
        keyword: 订单名称关键字(可选)
    
    Returns:
        可开票订单列表
    """
    try:
        # 可开票订单必须满足:can_invoice=1 且 status='delivered'
        filters = {"can_invoice": 1, "status": "delivered"}
        if keyword:
            filters["keyword"] = keyword
        
        orders = query_orders(user_id, **filters)
        
        if not orders:
            return "没有可开票的订单(只有已签收的订单才能开具发票)"
        
        # 格式化结果(orders已经是字典列表)
        for order in orders:
            order["order_date"] = order["order_date"].strftime("%Y-%m-%d")
        
        return str(orders)
    except Exception as e:
        logger.error(f"查询可开票订单失败: {e}")
        return f"查询可开票订单时出错: {str(e)}"


@tool
def issue_invoice(order_id: str) -> str:
    """开具发票
    
    Args:
        order_id: 订单ID
    
    Returns:
        发票开具结果
    """
    try:
        from smart_customer_service.database import get_order_by_id, update_order_invoice_status
        
        logger.debug(f"根据订单ID获取订单({order_id})")
        order = get_order_by_id(order_id)
        
        if not order:
            return f"未找到订单 {order_id[:8]}..."
        
        if order["can_invoice"] == 0:
            return f"订单【{order['order_name']}】不可开票"
        
        # 检查是否已开票
        if order.get("invoice_status") == "已开票":
            return f"订单【{order['order_name']}】已开具过发票,无需重复开具"
        
        # 更新发票状态
        update_order_invoice_status(order_id, "已开票")
        
        return f"订单【{order['order_name']}】发票已开具,将在3个工作日内寄出"
    except Exception as e:
        logger.error(f"开具发票失败: {e}")
        return f"开具发票时出错: {str(e)}"
