# models/user.py
from sqlalchemy import Column, Integer, String, TIMESTAMP, Enum
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username = Column(String(50), nullable=False, unique=True, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码（加密存储）")
    nickname = Column(String(50), nullable=True, comment="昵称")
    avatar = Column(String(255), nullable=True, comment="头像URL")
    gender = Column(Enum('male', 'female', 'unknown'), nullable=False, server_default='unknown', comment="性别")
    bio = Column(String(500), nullable=True, comment="个人简介")
    phone = Column(String(20), nullable=True, unique=True, comment="手机号")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")