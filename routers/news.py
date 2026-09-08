# routers/news.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database import get_db
from crud.news import get_news_list, get_news_by_id, increment_views
from schemas.common import ApiResponse
from schemas.news import (
    NewsOut, NewsDetail, NewsListResponse,
    CategoryBase, NewsQueryParams  # 复用之前的查询参数类（稍后调整）
)
from crud.news_category import get_categories  # 需要实现分类CRUD

router = APIRouter(prefix="/api/news", tags=["新闻"])


# ---------- 分类列表 ----------
@router.get("/categories", response_model=ApiResponse)
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """获取新闻分类列表"""
    categories = await get_categories(db, skip=skip, limit=limit)
    return ApiResponse(data=[CategoryBase.model_validate(c) for c in categories])


# ---------- 新闻列表（分页） ----------
@router.get("/list", response_model=ApiResponse)
async def list_news(
    categoryId: int = Query(..., description="分类ID（必填）"),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db)
):
    """获取指定分类的新闻列表（分页）"""
    params = NewsQueryParams(
        page=page,
        page_size=pageSize,
        category_id=categoryId,
        # 文档未提及keyword，可忽略
    )
    items, total = await get_news_list(db, params)
    # 转换为NewsOut
    out_items = [NewsOut.model_validate(item) for item in items]
    response_data = NewsListResponse.from_pagination(
        items=out_items,
        total=total,
        page=page,
        page_size=pageSize
    )
    return ApiResponse(data=response_data.model_dump())


# ---------- 新闻详情 ----------
@router.get("/detail", response_model=ApiResponse)
async def get_news_detail(
    id: int = Query(..., description="新闻ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取新闻详情（同时增加浏览量）"""
    news = await get_news_by_id(db, id)
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    # 增加浏览量（异步执行）
    await increment_views(db, id)
    await db.refresh(news)

    # 构建详情数据，related_news 暂时为空列表
    detail = NewsDetail(
        id=news.id,
        title=news.title,
        content=news.content,
        image=news.image,
        author=news.author,
        publish_time=news.publish_time,
        category_id=news.category_id,
        views=news.views,
        related_news=[]   # 后续可实现推荐逻辑
    )
    return ApiResponse(data=detail.model_dump())