"""数据库模型定义

使用SQLAlchemy ORM定义数据库表结构
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    user_id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(username='{self.username}')>"


class Conversation(Base):
    """对话记录模型"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(36), nullable=False)
    message_role = Column(String(20), nullable=False)  # user/assistant/system
    message_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="conversations")
    
    # 索引
    __table_args__ = (
        Index("idx_conv_user_session", "user_id", "session_id"),
    )
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, role='{self.message_role}')>"


class Order(Base):
    """订单模型(模拟数据)"""
    __tablename__ = "orders"
    
    order_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    order_name = Column(String(200), nullable=False)
    order_date = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending/shipped/delivered/cancelled
    logistics_status = Column(Text)
    can_refund = Column(Integer, default=1)  # SQLite uses INTEGER for boolean
    can_invoice = Column(Integer, default=1)
    invoice_status = Column(String(20), default="未开票")  # 未开票/已开票
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="orders")
    
    # 索引
    __table_args__ = (
        Index("idx_order_user_date", "user_id", "order_date"),
        Index("idx_order_name", "order_name"),
    )
    
    def __repr__(self):
        return f"<Order(order_id='{self.order_id}', name='{self.order_name}')>"
