"""Agent模块

提供基于ReAct的智能客服Agent
"""
from smart_customer_service.agents.react_agent import CustomerServiceReActAgent
from smart_customer_service.client import (
    speech_to_text,
    extract_order_number,
    test_aliyun_connection,
)
from .tools import create_customer_service_tools
from .tools.order_tools import (
    query_order_by_keyword,
    get_order_logistics,
    query_refundable_orders,
    submit_refund,
    query_invoiceable_orders,
    issue_invoice,
)

__all__ = [
    "CustomerServiceReActAgent",
    "create_customer_service_tools",
    "query_order_by_keyword",
    "get_order_logistics",
    "query_refundable_orders",
    "submit_refund",
    "query_invoiceable_orders",
    "issue_invoice",
    "speech_to_text",
    "extract_order_number",
    "test_aliyun_connection",
]
