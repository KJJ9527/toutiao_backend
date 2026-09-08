# crud/news_category.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.news_category import NewsCategory


async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    query = select(NewsCategory).order_by(NewsCategory.sort_order).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()