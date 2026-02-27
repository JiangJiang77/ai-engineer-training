"""数据库CRUD操作

提供数据库的增删改查功能
"""
import uuid
import bcrypt
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from smart_customer_service.config import settings
from smart_customer_service.database.models import Base, User, Conversation, Order
from smart_customer_service.utils import get_logger

logger = get_logger(__name__)

# 创建数据库引擎
engine = create_engine(settings.get_database_url(), echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session():
    """获取数据库会话(上下文管理器)"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_user(username: str, password: str) -> Dict[str, Any]:
    """创建用户"""
    with get_db_session() as session:
        # 检查用户是否已存在
        existing_user = session.query(User).filter(User.username == username).first()
        if existing_user:
            raise ValueError(f"User '{username}' already exists")
        
        # 密码加密
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # 创建用户
        user = User(
            user_id=str(uuid.uuid4()),
            username=username,
            password_hash=password_hash
        )
        session.add(user)
        session.flush()
        
        # 返回字典而不是ORM对象
        return {
            "user_id": user.user_id,
            "username": user.username,
            "created_at": user.created_at
        }


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """用户认证
    
    Args:
        username: 用户名
        password: 密码
    
    Returns:
        用户信息字典,认证失败返回None
    """
    with get_db_session() as session:
        user = session.query(User).filter(User.username == username).first()
        
        if not user:
            return None
        
        # 验证密码
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return None
        
        # 返回字典
        return {
            "user_id": user.user_id,
            "username": user.username,
            "created_at": user.created_at
        }


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """根据用户名查询用户"""
    with get_db_session() as session:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return None
        return {
            "user_id": user.user_id,
            "username": user.username,
            "password_hash": user.password_hash,
            "created_at": user.created_at
        }


def save_conversation(user_id: str, session_id: str, role: str, content: str) -> Conversation:
    """保存对话记录"""
    with get_db_session() as session:
        conversation = Conversation(
            conversation_id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            message_role=role,
            message_content=content
        )
        session.add(conversation)
        session.flush()
        return conversation


def get_conversation_history(user_id: str, session_id: str, limit: int = 50) -> List[Conversation]:
    """获取对话历史"""
    with get_db_session() as session:
        conversations = session.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.session_id == session_id
        ).order_by(Conversation.created_at.desc()).limit(limit).all()
        return list(reversed(conversations))


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
        logger.debug(f"[DB] 查询完成, 找到 {len(orders)} 个订单")

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
