# crud/favorite.py
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple, Optional

from models.favorite import Favorite
from models.news import News
from schemas.favorite import FavoriteItem


async def get_favorite_status(db: AsyncSession, user_id: int, news_id: int) -> bool:
    """检查用户是否收藏了某新闻"""
    stmt = select(Favorite.id).where(
        Favorite.user_id == user_id,
        Favorite.news_id == news_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def add_favorite(db: AsyncSession, user_id: int, news_id: int) -> Favorite:
    """添加收藏，如果已存在则忽略（或抛出异常）"""
    # 先检查是否已收藏
    exists = await get_favorite_status(db, user_id, news_id)
    if exists:
        raise ValueError("已经收藏过了")
    favorite = Favorite(user_id=user_id, news_id=news_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite


async def remove_favorite(db: AsyncSession, user_id: int, news_id: int) -> bool:
    """取消收藏，返回是否删除成功"""
    stmt = delete(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.news_id == news_id
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def clear_favorites(db: AsyncSession, user_id: int) -> int:
    """清空用户所有收藏，返回删除条数"""
    stmt = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


async def get_favorites_paginated(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 10
) -> Tuple[List[FavoriteItem], int]:
    """分页获取用户的收藏列表（含新闻信息）"""
    # 查询总数
    count_stmt = select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id)
    total = await db.scalar(count_stmt) or 0

    # 查询列表，联查新闻表
    offset = (page - 1) * page_size
    stmt = (
        select(
            Favorite.id,
            Favorite.created_at.label("favorite_time"),
            News.id.label("news_id"),
            News.title,
            News.description,
            News.image,
            News.author,
            News.publish_time,
            News.category_id,
            News.views
        )
        .join(News, Favorite.news_id == News.id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for row in rows:
        # 构造 FavoriteItem
        item = FavoriteItem(
            id=row.news_id,
            title=row.title,
            description=row.description,
            image=row.image,
            author=row.author,
            publish_time=row.publish_time,
            category_id=row.category_id,
            views=row.views,
            favorite_time=row.favorite_time
        )
        items.append(item)

    return items, total