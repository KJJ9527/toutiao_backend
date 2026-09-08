# models/favorite.py
from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class Favorite(Base):
    __tablename__ = "favorite"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="收藏ID")
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, comment="用户ID")
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, comment="新闻ID")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), comment="收藏时间")

    __table_args__ = (
        UniqueConstraint("user_id", "news_id", name="user_news_unique"),
    )