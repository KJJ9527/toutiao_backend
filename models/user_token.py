# models/user_token.py
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from database import Base

class UserToken(Base):
    __tablename__ = "user_token"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="令牌ID")
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, comment="用户ID")
    token = Column(String(255), nullable=False, unique=True, comment="令牌值")
    expires_at = Column(TIMESTAMP, nullable=False, comment="过期时间")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), comment="创建时间")