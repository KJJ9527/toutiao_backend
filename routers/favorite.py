# routers/favorite.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from crud.favorite import (
    get_favorite_status, add_favorite, remove_favorite,
    clear_favorites, get_favorites_paginated
)
from schemas.common import ApiResponse
from schemas.favorite import (
    FavoriteCheckResponse, AddFavoriteRequest,
    FavoriteListResponse, FavoriteItem
)

# 临时认证依赖（后续替换为真实认证）
# 这里简单模拟，假设当前用户ID为1（测试用）
async def get_current_user():
    # 实际应解析token，这里模拟
    return {"id": 1}

router = APIRouter(prefix="/api/favorite", tags=["收藏"])


@router.get("/check", response_model=ApiResponse)
async def check_favorite(
    newsId: int = Query(..., description="新闻ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """检查当前用户是否收藏了该新闻"""
    is_fav = await get_favorite_status(db, current_user["id"], newsId)
    return ApiResponse(data=FavoriteCheckResponse(isFavorite=is_fav).model_dump())


@router.post("/add", response_model=ApiResponse)
async def add_favorite_endpoint(
    req: AddFavoriteRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """添加收藏"""
    try:
        favorite = await add_favorite(db, current_user["id"], req.newsId)
        # 返回收藏记录（可返回完整对象或简略信息）
        return ApiResponse(message="收藏成功", data={
            "id": favorite.id,
            "userId": favorite.user_id,
            "newsId": favorite.news_id,
            "createTime": favorite.created_at.isoformat()
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/remove", response_model=ApiResponse)
async def remove_favorite_endpoint(
    newsId: int = Query(..., description="新闻ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """取消收藏"""
    deleted = await remove_favorite(db, current_user["id"], newsId)
    if not deleted:
        raise HTTPException(status_code=404, detail="未找到该收藏记录")
    return ApiResponse(message="取消收藏成功", data=None)


@router.get("/list", response_model=ApiResponse)
async def get_favorites_list(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页条数"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取收藏列表（分页）"""
    items, total = await get_favorites_paginated(db, current_user["id"], page, pageSize)
    hasMore = page * pageSize < total
    response_data = FavoriteListResponse(
        list=items,
        total=total,
        hasMore=hasMore
    )
    return ApiResponse(data=response_data.model_dump())


@router.delete("/clear", response_model=ApiResponse)
async def clear_favorites_endpoint(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """清空所有收藏"""
    deleted_count = await clear_favorites(db, current_user["id"])
    return ApiResponse(message=f"成功删除{deleted_count}条收藏记录", data=None)