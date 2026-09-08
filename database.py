# database.py (根目录)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from config.db_conf import db_settings


# 1. 创建 ORM 基类（所有 Model 必须继承它）
Base = declarative_base()

# 2.创建异步引擎（在此处调整你之前遇到的连接超时参数）
async_engine = create_async_engine(
    db_settings.DATABASE_URL,
    pool_size=db_settings.POOL_SIZE,
    max_overflow=db_settings.MAX_OVERFLOW,
    pool_recycle=db_settings.POOL_RECYCLE,
    pool_pre_ping=True,          # 自动检测连接是否存活（强烈推荐）
    connect_args={
        "connect_timeout": 60,   # 针对MySQL连接超时（对应你之前的30s问题）
    }
)
# 3. 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind= async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 4.依赖项，用于获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

__all__ = ["Base", "async_engine", "AsyncSessionLocal", "get_db"]

