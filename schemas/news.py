# schemas/news.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any


# ---------- 基础模型 ----------
class CategoryBase(BaseModel):
    id: int
    name: str
    sort_order: Optional[int] = 0

    class Config:
        from_attributes = True


class NewsOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    author: Optional[str] = None
    views: int
    publish_time: datetime
    category_id: int   # 文档中列表返回包含 category_id
    category: Optional[CategoryBase] = None  # 可嵌套分类信息

    class Config:
        from_attributes = True


class NewsDetail(BaseModel):
    id: int
    title: str
    content: str
    image: Optional[str] = None
    author: Optional[str] = None
    publish_time: datetime
    category_id: int
    views: int
    related_news: List[Any] = []   # 暂时为空列表，后续实现推荐逻辑

    class Config:
        from_attributes = True


# ---------- 分页响应 ----------
class NewsListResponse(BaseModel):
    list: List[NewsOut]
    total: int
    hasMore: bool

    @classmethod
    def from_pagination(cls, items: List[NewsOut], total: int, page: int, page_size: int):
        hasMore = page * page_size < total
        return cls(list=items, total=total, hasMore=hasMore)


# schemas/news.py（在文件末尾添加）

class NewsQueryParams(BaseModel):
    """新闻列表查询参数"""
    page: int = 1
    page_size: int = 10
    category_id: Optional[int] = None
    keyword: Optional[str] = None