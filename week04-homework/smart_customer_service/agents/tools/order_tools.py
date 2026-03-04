"""订单相关工具

提供订单查询、退款、发票等功能
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain.tools import tool

from smart_customer_service.repository import query_orders, update_order_status
from smart_customer_service.utils import parse_relative_time, get_logger

logger = get_logger(__name__)

@tool
def query_order_by_keyword(user_id: str, keyword: str, date_str: Optional[str] = None) -> str:
    """订单查询(关键字+日期)。输入: user_id, keyword, date_str(可选,如"昨天"/"今天")。输出: 订单列表或提示。"""
    try:
        filters = {"keyword": keyword}
        
        # 解析日期
        if date_str:
            order_date = parse_relative_time(date_str)
            filters["order_date"] = order_date.date()
        
        orders = query_orders(user_id, filters=filters)
        
        if not orders:
            return f"未找到包含'{keyword}'的订单"
        
        # 格式化结果(避免修改原始订单对象)
        formatted = []
        for order in orders:
            order_copy = order.copy()
            order_copy["order_date"] = order_copy["order_date"].strftime("%Y-%m-%d")
            formatted.append(order_copy)
        
        return str(formatted)
    except Exception as e:
        logger.error(f"查询订单失败: {e}", exc_info=True)
        return f"查询订单时出错: {str(e)}"


@tool
def query_orders_by_date(user_id: str, date_str: str) -> str:
    """订单查询(按日期)。输入: user_id, date_str(如"昨天"/"今天")。输出: 订单列表或提示。"""
    try:
        # 解析日期
        order_date = parse_relative_time(date_str)
        
        orders = query_orders(user_id, filters={"order_date": order_date.date()})
        
        if not orders:
            return f"{date_str}没有订单"
        
        # 格式化结果(避免修改原始订单对象)
        formatted = []
        for order in orders:
            order_copy = order.copy()
            order_copy["order_date"] = order_copy["order_date"].strftime("%Y-%m-%d")
            formatted.append(order_copy)
        
        return str(formatted)
    except Exception as e:
        logger.error(f"查询订单失败: {e}", exc_info=True)
        return f"查询订单时出错: {str(e)}"


@tool
def get_order_logistics(order_id: str) -> str:
    """获取订单物流状态。输入: order_id。输出: 物流状态或提示。"""
    try:
        from smart_customer_service.repository import get_order_by_id

        order = get_order_by_id(order_id)
        if not order:
            return f"未找到订单 {order_id}"

        return (
            f"订单【{order['order_name']}】\n"
            f"物流状态: {order['logistics_status']}\n"
            f"订单状态: {order['status']}"
        )
    except Exception as e:
        logger.error(f"获取物流状态失败: {e}", exc_info=True)
        return f"获取物流状态时出错: {str(e)}"


@tool
def query_refundable_orders(user_id: str) -> str:
    """查询可退款订单。输入: user_id。输出: 可退款订单列表或提示。"""
    try:
        orders = query_orders(user_id, filters={"can_refund": 1})
        
        if not orders:
            return "没有可退款的订单"
        
        # 格式化结果(避免修改原始订单对象)
        formatted = []
        for order in orders:
            order_copy = order.copy()
            order_copy["order_date"] = order_copy["order_date"].strftime("%Y-%m-%d")
            formatted.append(order_copy)
        
        return str(formatted)
    except Exception as e:
        logger.error(f"查询可退款订单失败: {e}", exc_info=True)
        return f"查询可退款订单时出错: {str(e)}"


@tool
def submit_refund(order_id: str) -> str:
    """提交退款申请。输入: order_id。输出: 退款处理结果或提示。"""
    try:
        from smart_customer_service.repository import get_order_by_id

        order = get_order_by_id(order_id)
        if not order:
            return f"未找到订单 {order_id}"

        if order["can_refund"] == 0:
            return f"订单【{order['order_name']}】不支持退款"

        updated = update_order_status(order_id, "refunding")
        return f"订单【{updated.order_name}】退款申请已提交,预计3-5个工作日退款到账"
    except Exception as e:
        logger.error(f"提交退款失败: {e}", exc_info=True)
        return f"提交退款时出错: {str(e)}"


@tool
def query_invoiceable_orders(user_id: str, keyword: Optional[str] = None) -> str:
    """查询可开票订单。输入: user_id, keyword(可选)。输出: 可开票订单列表或提示。规则: 仅已签收订单可开票。"""
    try:
        # 可开票订单必须满足:can_invoice=1 且 status='delivered'
        filters = {"can_invoice": 1, "status": "delivered"}
        if keyword:
            filters["keyword"] = keyword
        
        orders = query_orders(user_id, filters=filters)
        
        if not orders:
            return "没有可开票的订单(只有已签收的订单才能开具发票)"
        
        # 格式化结果(避免修改原始订单对象)
        formatted = []
        for order in orders:
            order_copy = order.copy()
            order_copy["order_date"] = order_copy["order_date"].strftime("%Y-%m-%d")
            formatted.append(order_copy)
        
        return str(formatted)
    except Exception as e:
        logger.error(f"查询可开票订单失败: {e}", exc_info=True)
        return f"查询可开票订单时出错: {str(e)}"


@tool
def issue_invoice(order_id: str) -> str:
    """开具发票。输入: order_id。输出: 发票开具结果或提示。"""
    try:
        from smart_customer_service.repository import get_order_by_id, update_order_invoice_status
        
        logger.debug(f"根据订单ID获取订单({order_id})")
        order = get_order_by_id(order_id)
        
        if not order:
            return f"未找到订单 {order_id}"
        
        if order["can_invoice"] == 0:
            return f"订单【{order['order_name']}】不可开票"
        
        # 检查是否已开票
        if order.get("invoice_status") == "已开票":
            return f"订单【{order['order_name']}】已开具过发票,无需重复开具"
        
        # 更新发票状态
        update_order_invoice_status(order_id, "已开票")
        
        return f"订单【{order['order_name']}】发票已开具,将在3个工作日内寄出"
    except Exception as e:
        logger.error(f"开具发票失败: {e}", exc_info=True)
        return f"开具发票时出错: {str(e)}"


def create_order_tools(user_id: str) -> list:
    """创建订单相关工具列表 (绑定 user_id)"""

    @tool
    def query_orders_tool(params_str: str) -> str:
        """查询用户订单。输入: keyword=商品名,date=时间(可选)。示例: keyword=笔记本,date=昨天 或 date=昨天 或 keyword=笔记本 或 空字符串。"""
        try:
            params = {}
            if params_str.strip():
                for item in params_str.split(","):
                    if "=" in item:
                        k, v = item.split("=", 1)
                        params[k.strip()] = v.strip()

            keyword = params.get("keyword")
            date_str = params.get("date")

            if keyword:
                return query_order_by_keyword.invoke(
                    {"user_id": user_id, "keyword": keyword, "date_str": date_str}
                )
            if date_str:
                return query_orders_by_date.invoke(
                    {"user_id": user_id, "date_str": date_str}
                )

            return query_order_by_keyword.invoke(
                {"user_id": user_id, "keyword": "", "date_str": None}
            )

        except Exception as e:
            logger.error(f"[Tool Error] QueryOrders: {e}", exc_info=True)
            return f"查询订单失败: {str(e)}"

    @tool
    def get_logistics_tool(order_id: str) -> str:
        """获取订单物流信息。输入: 订单号(UUID)。示例: 33ca60d5-3d02-4df1-97f6-daba79a7e294。"""
        try:
            order_id = order_id.strip()
            logger.debug(f"[Tool] GetLogistics: order_id={order_id}")
            return get_order_logistics.invoke({"order_id": order_id})

        except Exception as e:
            logger.error(f"[Tool Error] GetLogistics: {e}", exc_info=True)
            return f"获取物流信息失败: {str(e)}"

    @tool
    def submit_refund_tool(order_id: str) -> str:
        """提交退款申请。输入: 订单号(UUID)。注意: 只有可退款的订单才能提交退款。"""
        try:
            order_id = order_id.strip()
            logger.debug(f"[Tool] SubmitRefund: order_id={order_id}")
            return submit_refund.invoke({"order_id": order_id})

        except Exception as e:
            logger.error(f"[Tool Error] SubmitRefund: {e}", exc_info=True)
            return f"提交退款失败: {str(e)}"

    @tool
    def issue_invoice_tool(order_id: str) -> str:
        """开具发票。输入: 订单号(UUID)。注意: 只有已签收的订单才能开具发票。"""
        try:
            order_id = order_id.strip()
            logger.debug(f"[Tool] IssueInvoice: order_id={order_id}")
            return issue_invoice.invoke({"order_id": order_id})

        except Exception as e:
            logger.error(f"[Tool Error] IssueInvoice: {e}", exc_info=True)
            return f"开具发票失败: {str(e)}"

    tools = [
        query_orders_tool,
        get_logistics_tool,
        submit_refund_tool,
        issue_invoice_tool,
    ]

    logger.debug(f"创建了 {len(tools)} 个订单工具: {[t.name for t in tools]}")

    return tools
