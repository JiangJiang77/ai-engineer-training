
from langchain.tools import tool
from langgraph_demo.order_repo import get_order_by_id

@tool
def get_order_detail(order_id: str) -> str:
    """
    获取订单详情
    """

    print(f"--- [工具调用] 正在查询订单号: {order_id} ---")
    order_info = get_order_by_id(order_id)
    # return order_info
    if not order_info:
        return f"未找到订单号: {order_id},请检查订单号是否正确"
        
    return f"""订单号: {order_id},
        订单编号: {order_info['order_id']},
        订单名称: {order_info['order_name']},
        订单状态: {order_info['status']},
        物流状态: {order_info['logistics_status']}"""
