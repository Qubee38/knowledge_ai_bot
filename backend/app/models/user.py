"""
ユーザーモデル（SQLAlchemy）
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

# 注意: Base定義は別ファイルで管理することを推奨
# ここでは簡易的に記載
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """ユーザーテーブル"""
    
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<User {self.email}>"