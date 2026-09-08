# models/news_category.py
from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from database import Base

class NewsCategory(Base):
    __tablename__ = "news_category"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="分类ID")
    name = Column(String(50), nullable=False, unique=True, comment="分类名称")
    sort_order = Column(Integer, nullable=False, server_default="0", comment="排序顺序")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")