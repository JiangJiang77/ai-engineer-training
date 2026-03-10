"""订单查询与展示服务

为工作流节点提供统一的订单筛选和格式化能力。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from smart_customer_service_extend.repository import query_orders

STATUS_MAP = {
    "pending": "待处理",
    "shipped": "已发货",
    "delivered": "已签收",
    "cancelled": "已取消",
}


def build_keyword(context: Dict[str, Any]) -> Optional[str]:
    """从上下文中构造查询关键字(优先keyword, 其次item, 最后brand)"""
    return context.get("keyword") or context.get("item") or context.get("brand")


def build_filters(
    context: Dict[str, Any],
    *,
    include_keyword: bool = True,
    include_date: bool = True,
    extra_filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """根据上下文构建查询过滤条件"""
    filters: Dict[str, Any] = {}

    if include_keyword:
        keyword = build_keyword(context)
        if keyword:
            filters["keyword"] = keyword

    if include_date and context.get("date"):
        filters["order_date"] = context["date"]

    if extra_filters:
        filters.update(extra_filters)

    return filters


def fetch_orders_by_context(
    user_id: str,
    context: Dict[str, Any],
    *,
    include_keyword: bool = True,
    include_date: bool = True,
    extra_filters: Optional[Dict[str, Any]] = None,
) -> list[Dict[str, Any]]:
    """按上下文查询订单"""
    filters = build_filters(
        context,
        include_keyword=include_keyword,
        include_date=include_date,
        extra_filters=extra_filters,
    )
    if filters:
        return query_orders(user_id, filters=filters)
    return query_orders(user_id)


def format_order_date(value: Any) -> str:
    """格式化订单日期"""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)


def format_order_card(order: Dict[str, Any], *, include_logistics: bool = True) -> str:
    """格式化单个订单卡片文本"""
    status_cn = STATUS_MAP.get(order.get("status"), order.get("status", "未知"))
    lines = [
        f"- 订单号: {order.get('order_id', '未知')}",
        f"  商品: {order.get('order_name', '未知')}",
        f"  日期: {format_order_date(order.get('order_date', '未知'))}",
        f"  状态: {status_cn}",
    ]
    if include_logistics:
        lines.append(f"  物流: {order.get('logistics_status', '暂无物流信息')}")
    lines.append(f"  发票: {order.get('invoice_status', '未开票')}")
    return "\n".join(lines)


def format_orders(orders: list[Dict[str, Any]], *, include_logistics: bool = True) -> str:
    """格式化订单列表文本"""
    return "\n\n".join(
        format_order_card(order, include_logistics=include_logistics) for order in orders
    )
