# crud/news.py
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime

from models.news import News
from models.news_category import NewsCategory
from schemas.news import NewsQueryParams, NewsOut, NewsDetail
from utils.cache import get_cache, set_cache, delete_cache, delete_cache_pattern, get_redis


# ---------- 工具函数：获取/更新浏览量 ----------
async def get_news_views(news_id: int) -> int:
    """从 Redis 获取浏览量，若不存在则返回 0"""
    redis = get_redis()
    views = await redis.get(f"news:views:{news_id}")
    if views is None:
        return 0
    return int(views)

async def increment_views(news_id: int) -> int:
    """增加浏览量，返回新值"""
    redis = get_redis()
    new_views = await redis.incr(f"news:views:{news_id}")
    # 如果首次设置，设置过期时间（可选，避免无限增长）
    # await redis.expire(f"news:views:{news_id}", 86400 * 30)  # 30天
    return new_views

async def sync_views_to_db(db: AsyncSession, news_id: int):
    """将 Redis 中的浏览量同步到数据库（可选，在定时任务中执行）"""
    views = await get_news_views(news_id)
    if views > 0:
        await db.execute(
            News.__table__.update()
            .where(News.id == news_id)
            .values(views=views)
        )
        await db.commit()


# ---------- 缓存辅助：生成缓存键 ----------
def _list_cache_key(params: NewsQueryParams) -> str:
    return f"news:list:cat_{params.category_id or 0}:page_{params.page}:size_{params.page_size}:kw_{params.keyword or ''}"


# ---------- 获取新闻列表（带缓存） ----------
async def get_news_list(
    db: AsyncSession,
    params: NewsQueryParams
) -> Tuple[List[NewsOut], int]:
    """返回 (新闻列表, 总数)，列表元素为 NewsOut 对象"""
    cache_key = _list_cache_key(params)

    # 1. 尝试从缓存获取
    cached = await get_cache(cache_key)
    if cached is not None:
        # 缓存中存储的是序列化后的字典列表，需要转回 NewsOut 对象
        items_data = cached["items"]
        total = cached["total"]
        # 将字典转为 NewsOut 对象（注意：此时 views 可能来自缓存，但需要从 Redis 实时获取？）
        # 我们选择缓存时存储 views，但在返回时可以用 Redis 刷新 views（可选）
        # 这里直接使用缓存的 views，因为它是查询时从 DB 读取的，可能不是最新。
        # 小型项目可以接受，若要更准，可以在返回前从 Redis 获取最新 views。
        items = [NewsOut(**item) for item in items_data]
        return items, total

    # 2. 数据库查询
    query = select(News).join(NewsCategory, News.category_id == NewsCategory.id)
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

    query = query.order_by(News.publish_time.desc())
    offset = (params.page - 1) * params.page_size
    query = query.offset(offset).limit(params.page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    # 计数
    count_query = select(func.count()).select_from(News)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query) or 0

    # 3. 序列化为字典（包含 views，但 views 是 DB 中的值）
    items_serialized = [NewsOut.model_validate(item).model_dump() for item in items]

    # 4. 存入缓存（过期 300 秒）
    cache_data = {"items": items_serialized, "total": total}
    await set_cache(cache_key, cache_data, expire=300)

    # 5. 返回 NewsOut 对象（方便路由直接使用）
    return [NewsOut(**item) for item in items_serialized], total


# ---------- 获取新闻详情（带缓存） ----------
async def get_news_by_id(db: AsyncSession, news_id: int) -> Optional[NewsDetail]:
    """返回 NewsDetail 对象，views 字段会从 Redis 读取最新值"""
    cache_key = f"news:detail:{news_id}"

    # 1. 尝试从缓存获取
    cached = await get_cache(cache_key)
    if cached is not None:
        # 检查是否是空值标记
        if cached.get("_empty"):
            return None
        # 构建 NewsDetail 对象，但 views 可能不是最新的，从 Redis 获取
        detail_dict = cached
        # 从 Redis 获取最新 views
        views = await get_news_views(news_id)
        if views > 0:
            detail_dict["views"] = views
        return NewsDetail(**detail_dict)

    # 2. 数据库查询
    query = select(News).where(News.id == news_id).join(NewsCategory, News.category_id == NewsCategory.id)
    result = await db.execute(query)
    news = result.scalar_one_or_none()
    if not news:
        # 缓存空值 60 秒
        await set_cache(cache_key, {"_empty": True}, expire=60)
        return None

    # 3. 序列化（先不包含 views，稍后从 Redis 读取）
    serialized = NewsDetail.model_validate(news).model_dump()
    # 从 Redis 获取浏览量（如果不存在，则使用 DB 中的值）
    views = await get_news_views(news_id)
    if views == 0:
        # 如果 Redis 中没有，将 DB 中的 views 写入 Redis
        views = news.views
        await set_cache(f"news:views:{news_id}", views, expire=None)  # 长期保存
    serialized["views"] = views

    # 4. 存入缓存（过期 600 秒）
    await set_cache(cache_key, serialized, expire=600)

    return NewsDetail(**serialized)


# ---------- 缓存失效工具 ----------
async def clear_news_cache(news_id: Optional[int] = None, category_id: Optional[int] = None):
    """
    清除新闻相关缓存。
    - 如果传 news_id：清除该新闻详情缓存。
    - 如果传 category_id：清除该分类下的所有列表缓存。
    - 如果都不传：清除所有新闻缓存（慎用）。
    """
    if news_id:
        await delete_cache(f"news:detail:{news_id}")
    if category_id is not None:
        await delete_cache_pattern(f"news:list:cat_{category_id}:*")
    if news_id is None and category_id is None:
        # 清除所有新闻列表和详情缓存（谨慎）
        await delete_cache_pattern("news:list:*")
        # 详情缓存无法按模式批量删除，除非用前缀，我们可另外处理
        # 这里只清除列表