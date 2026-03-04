"""数据库CRUD操作

提供数据库的增删改查功能
"""
import uuid
import bcrypt
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from smart_customer_service.repository.models import Base, User, Conversation, Order
from smart_customer_service.utils import get_logger
from smart_customer_service.repository.db import get_db_session

logger = get_logger(__name__)

def get_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    """根据订单ID获取订单
    
    Args:
        order_id: 订单ID
    
    Returns:
        订单信息字典,未找到返回None
    """
    logger.debug(f"根据订单ID获取订单({order_id})")
    with get_db_session() as session:
        order = session.query(Order).filter(Order.order_id == order_id).first()
        
        if not order:
            return None
        
        return {
            "order_id": order.order_id,
            "order_name": order.order_name,
            "status": order.status,
            "logistics_status": order.logistics_status,
            "order_date": order.order_date,
            "can_refund": order.can_refund,
            "can_invoice": order.can_invoice,
            "invoice_status": order.invoice_status
        }


def query_orders(user_id: str, filters: Optional[Dict[str, Any]] = None, **kwargs) -> List[Dict[str, Any]]:
    """查询订单
    
    Args:
        user_id: 用户ID
        filters: 过滤条件字典 (可选)
        **kwargs: 额外的过滤条件, 支持:
            - order_date: 订单日期(date对象)
            - keyword: 订单名称关键字
            - status: 订单状态
            - can_refund: 是否可退款
            - can_invoice: 是否可开票
    
    Returns:
        订单列表
    """
    from sqlalchemy import func
    
    with get_db_session() as session:
        logger.debug(f"[DB] 开始查询订单, user_id: {user_id}")
        query = session.query(Order).filter(Order.user_id == user_id)
        
        # 合并 filters 和 kwargs
        if filters is None:
            filters = {}
        else:
            # 避免修改原始字典, 创建副本
            filters = filters.copy()
        
        filters.update(kwargs)
        logger.debug(f"[DB] 过滤条件: {filters}")
        
        # 应用过滤条件
        if "order_date" in filters:
            # 使用func.date()提取日期部分进行比较
            target_date = filters["order_date"]
            query = query.filter(func.date(Order.order_date) == target_date)
        
        if "keyword" in filters:
            query = query.filter(Order.order_name.like(f"%{filters['keyword']}%"))
        
        if "status" in filters:
            query = query.filter(Order.status == filters["status"])
        
        if "can_refund" in filters:
            query = query.filter(Order.can_refund == filters["can_refund"])
        
        if "can_invoice" in filters:
            query = query.filter(Order.can_invoice == filters["can_invoice"])
        
        orders = query.all()
        logger.debug(f"[DB] 查询完成, 找到 {len(orders)} 个符合条件的订单")

        if not orders and not filters:
            # 如果没找到订单且没加过滤条件，查一下数据库里到底有哪些 user_id 有订单
            all_user_ids = [r[0] for r in session.query(Order.user_id).distinct().all()]
            logger.debug(f"[DB] 调试: 数据库中拥有订单的用户 ID 列表: {all_user_ids}")
        
        # 转换为字典列表
        return [
            {
                "order_id": order.order_id,
                "order_name": order.order_name,
                "status": order.status,
                "logistics_status": order.logistics_status,
                "order_date": order.order_date,
                "can_refund": order.can_refund,
                "can_invoice": order.can_invoice,
                "invoice_status": order.invoice_status
            }
            for order in orders
        ]


def update_order_status(order_id: str, status: str) -> Optional[Order]:
    """更新订单状态"""
    with get_db_session() as session:
        order = session.query(Order).filter(Order.order_id == order_id).first()
        if order:
            order.status = status
            session.flush()
        return order


def delete_order(order_id: str) -> bool:
    """删除订单
    
    Args:
        order_id: 订单ID
    
    Returns:
        是否删除成功
    """
    with get_db_session() as session:
        order = session.query(Order).filter(Order.order_id == order_id).first()
        if order:
            session.delete(order)
            session.commit()
            return True
        return False


def update_order_invoice_status(order_id: str, invoice_status: str = "已开票") -> bool:
    """更新订单发票状态
    
    Args:
        order_id: 订单ID
        invoice_status: 发票状态,默认"已开票"
    
    Returns:
        是否更新成功
    """
    with get_db_session() as session:
        order = session.query(Order).filter(Order.order_id == order_id).first()
        if order:
            order.invoice_status = invoice_status
            session.commit()
            return True
        return False


def create_order(user_id: str, order_name: str, order_date: datetime, **kwargs) -> Order:
    """创建订单(用于测试数据)"""
    with get_db_session() as session:
        # 如果 kwargs 中已经有了 order_id，则使用它，否则生成一个新的
        order_id = kwargs.pop('order_id', str(uuid.uuid4()))
        order = Order(
            order_id=order_id,
            user_id=user_id,
            order_name=order_name,
            order_date=order_date,
            **kwargs
        )
        session.add(order)
        session.flush()
        return order
