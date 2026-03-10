"""数据库CRUD操作

提供数据库的增删改查功能
"""
import uuid
import bcrypt
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from smart_customer_service_extend.repository.models import Base, User, Conversation, Order
from smart_customer_service_extend.utils import get_logger
from smart_customer_service_extend.repository.db import get_db_session

logger = get_logger(__name__)

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
