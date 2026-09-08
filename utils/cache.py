# utils/cache.py
import json
from typing import Optional, Any
from redis.asyncio import Redis
from config.cache_conf import cache_settings

redis_client: Optional[Redis] = None
redis_available: bool = False  # 标志 Redis 是否可用

async def init_redis():
    """初始化 Redis 连接，失败时降级（不抛出异常）"""
    global redis_client, redis_available
    try:
        redis_client = Redis(
            host=cache_settings.REDIS_HOST,
            port=cache_settings.REDIS_PORT,
            db=cache_settings.REDIS_DB,
            password=cache_settings.REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=2,  # 快速失败
        )
        await redis_client.ping()
        redis_available = True
        print("✅ Redis connected successfully")
    except Exception as e:
        redis_client = None
        redis_available = False
        print(f"⚠️ Redis connection failed: {e}. Caching disabled.")

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None

def get_redis() -> Redis:
    if redis_client is None:
        raise RuntimeError("Redis not initialized")
    return redis_client

# ---------- 缓存操作（自动检查可用性） ----------
async def set_cache(key: str, value: Any, expire: int = None):
    if not redis_available or redis_client is None:
        return
    try:
        if expire is None:
            expire = cache_settings.CACHE_DEFAULT_TIMEOUT
        await redis_client.setex(key, expire, json.dumps(value, default=str))
    except Exception:
        pass  # 静默失败，不影响主流程

async def get_cache(key: str) -> Optional[Any]:
    if not redis_available or redis_client is None:
        return None
    try:
        data = await redis_client.get(key)
        if data is None:
            return None
        return json.loads(data)
    except Exception:
        return None

async def delete_cache(key: str):
    if not redis_available or redis_client is None:
        return
    try:
        await redis_client.delete(key)
    except Exception:
        pass

async def delete_cache_pattern(pattern: str):
    if not redis_available or redis_client is None:
        return
    try:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
    except Exception:
        pass