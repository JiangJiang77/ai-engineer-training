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
