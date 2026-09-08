# crud/history.py
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple, List

from models.history import History
from models.news import News
from schemas.history import HistoryItem


async def add_history(db: AsyncSession, user_id: int, news_id: int) -> History:
    """添加浏览记录（每次浏览都插入新记录）"""
    history = History(user_id=user_id, news_id=news_id)
    db.add(history)
    await db.commit()
    await db.refresh(history)
    return history


async def get_history_list(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 10
) -> Tuple[List[HistoryItem], int]:
    """分页获取用户浏览历史（按浏览时间倒序）"""
    # 查询总数
    count_stmt = select(func.count()).select_from(History).where(History.user_id == user_id)
    total = await db.scalar(count_stmt) or 0

    # 查询列表（联查新闻表）
    offset = (page - 1) * page_size
    stmt = (
        select(
            History.id.label("history_id"),
            History.view_time,
            News.id,
            News.title,
            News.description,
            News.image,
            News.author,
            News.publish_time,
            News.category_id,
            News.views
        )
        .join(News, History.news_id == News.id)
        .where(History.user_id == user_id)
        .order_by(History.view_time.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for row in rows:
        item = HistoryItem(
            id=row.id,
            title=row.title,
            description=row.description,
            image=row.image,
            author=row.author,
            publish_time=row.publish_time,
            category_id=row.category_id,
            views=row.views,
            view_time=row.view_time
        )
        items.append(item)

    return items, total


async def delete_history_by_id(db: AsyncSession, user_id: int, history_id: int) -> bool:
    """删除单条浏览记录（校验所属用户）"""
    stmt = delete(History).where(
        and_(
            History.id == history_id,
            History.user_id == user_id
        )
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def clear_history(db: AsyncSession, user_id: int) -> int:
    """清空用户所有浏览记录，返回删除条数"""
    stmt = delete(History).where(History.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount