# routers/history.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from crud.history import (
    add_history, get_history_list,
    delete_history_by_id, clear_history
)
from schemas.common import ApiResponse
from schemas.history import (
    AddHistoryRequest, AddHistoryResponse,
    HistoryListResponse, HistoryItem
)
from utils.auth import get_current_user

router = APIRouter(prefix="/api/history", tags=["浏览历史"])


@router.post("/add", response_model=ApiResponse)
async def add_history_endpoint(
    req: AddHistoryRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """添加浏览记录"""
    history = await add_history(db, current_user.id, req.newsId)
    response_data = AddHistoryResponse(
        id=history.id,
        userId=history.user_id,
        newsId=history.news_id,
        viewTime=history.view_time
    )
    return ApiResponse(message="添加成功", data=response_data.model_dump())


@router.get("/list", response_model=ApiResponse)
async def get_history_list_endpoint(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页条数"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取浏览历史列表（分页）"""
    items, total = await get_history_list(db, current_user.id, page, pageSize)
    hasMore = page * pageSize < total
    response_data = HistoryListResponse(list=items, total=total, hasMore=hasMore)
    return ApiResponse(data=response_data.model_dump())


@router.delete("/delete/{history_id}", response_model=ApiResponse)
async def delete_history_endpoint(
    history_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除单条浏览记录"""
    deleted = await delete_history_by_id(db, current_user.id, history_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="记录不存在或无权删除")
    return ApiResponse(message="删除成功", data=None)


@router.delete("/clear", response_model=ApiResponse)
async def clear_history_endpoint(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """清空浏览历史"""
    deleted_count = await clear_history(db, current_user.id)
    return ApiResponse(message=f"清空成功，共删除{deleted_count}条记录", data=None)