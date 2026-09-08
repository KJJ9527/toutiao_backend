# models/history.py
from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey, Index
from sqlalchemy.sql import func
from database import Base

class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="历史ID")
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, comment="用户ID")
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, comment="新闻ID")
    view_time = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), comment="浏览时间")

    __table_args__ = (
        Index("fk_history_user_idx", "user_id"),
        Index("fk_history_news_idx", "news_id"),
        Index("idx_view_time", "view_time"),
    )