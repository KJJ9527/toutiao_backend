# models/news.py
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base  # 从根目录的 database.py 导入 Base


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="新闻ID")
    title = Column(String(255), nullable=False, comment="新闻标题")
    description = Column(String(500), nullable=True, comment="新闻简介")
    content = Column(Text, nullable=False, comment="新闻内容")
    image = Column(String(255), nullable=True, comment="封面图片URL")
    author = Column(String(50), nullable=True, comment="作者")
    category_id = Column(Integer, ForeignKey("news_category.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, comment="分类ID")
    views = Column(Integer, nullable=False, server_default="0", comment="浏览量")
    publish_time = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), comment="发布时间")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")

    # 关联分类表（方便联查分类名称）
    category = relationship("NewsCategory", lazy="joined")  # 默认联查，避免 N+1

    __table_args__ = (
        Index("fk_news_category_idx", "category_id"),
        Index("idx_publish_time", "publish_time"),
    )