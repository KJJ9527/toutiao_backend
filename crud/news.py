# crud/news.py
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Tuple

from models.news import News
from models.news_category import NewsCategory
from schemas.news import NewsQueryParams


async def get_news_list(
    db: AsyncSession,
    params: NewsQueryParams
) -> Tuple[list[News], int]:
    """
    分页获取新闻列表，支持分类筛选、关键词搜索。
    返回 (新闻列表, 总记录数)
    """
    query = select(News).join(NewsCategory, News.category_id == NewsCategory.id)

    # 过滤条件
    conditions = []
    if params.category_id:
        conditions.append(News.category_id == params.category_id)
    if params.keyword:
        keyword = f"%{params.keyword}%"
        conditions.append(
            or_(
                News.title.like(keyword),
                News.description.like(keyword)
            )
        )
    if conditions:
        query = query.where(and_(*conditions))

    # 排序（按发布时间倒序）
    query = query.order_by(News.publish_time.desc())

    # 分页
    offset = (params.page - 1) * params.page_size
    query = query.offset(offset).limit(params.page_size)

    # 执行查询
    result = await db.execute(query)
    items = result.scalars().all()

    # 获取总数（注意：用另一个独立的 select 来计数）
    count_query = select(func.count()).select_from(News)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query)

    return items, total or 0


async def get_news_by_id(db: AsyncSession, news_id: int) -> Optional[News]:
    """根据 ID 获取单条新闻（详情）"""
    query = select(News).where(News.id == news_id).join(NewsCategory, News.category_id == NewsCategory.id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 可选：增加浏览量（每次查看详情时调用）
async def increment_views(db: AsyncSession, news_id: int) -> None:
    """增加新闻浏览量（原子操作）"""
    await db.execute(
        News.__table__.update()
        .where(News.id == news_id)
        .values(views=News.views + 1)
    )
    await db.commit()