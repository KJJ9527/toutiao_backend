# schemas/history.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# 添加浏览记录请求
class AddHistoryRequest(BaseModel):
    newsId: int

# 浏览历史中的新闻信息（用于列表）
class HistoryNewsInfo(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    author: Optional[str] = None
    publish_time: datetime
    category_id: int
    views: int

    class Config:
        from_attributes = True

# 浏览历史列表项（包含新闻信息和浏览时间）
class HistoryItem(HistoryNewsInfo):
    view_time: datetime   # 对应 view_time

# 浏览历史列表响应
class HistoryListResponse(BaseModel):
    list: List[HistoryItem]
    total: int
    hasMore: bool

# 添加浏览记录响应（可选）
class AddHistoryResponse(BaseModel):
    id: int
    userId: int
    newsId: int
    viewTime: datetime