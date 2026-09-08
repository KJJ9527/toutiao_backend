# schemas/favorite.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any

# 收藏新闻的简要信息（用于列表返回）
class FavoriteNewsInfo(BaseModel):
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

# 收藏列表中的每一项（包含新闻信息和收藏时间）
class FavoriteItem(FavoriteNewsInfo):
    favorite_time: datetime   # 对应 created_at

# 收藏列表响应
class FavoriteListResponse(BaseModel):
    list: List[FavoriteItem]
    total: int
    hasMore: bool

# 检查收藏状态响应
class FavoriteCheckResponse(BaseModel):
    isFavorite: bool

# 添加收藏请求
class AddFavoriteRequest(BaseModel):
    newsId: int

