"""
ロールモデル（SQLAlchemy）
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from .user import Base


class Role(Base):
    """ロールテーブル"""
    
    __tablename__ = 'roles'
    __table_args__ = {'schema': 'public'}
    
    role_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100))
    description = Column(Text)
    is_system_role = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Role {self.role_name}>"


class UserRole(Base):
    """ユーザーロール紐付けテーブル"""
    
    __tablename__ = 'user_roles'
    __table_args__ = {'schema': 'public'}
    
    user_role_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('public.users.user_id', ondelete='CASCADE'), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey('public.roles.role_id', ondelete='CASCADE'), nullable=False)
    
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<UserRole user={self.user_id} role={self.role_id}>"