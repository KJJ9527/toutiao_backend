# crud/user_token.py
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from models.user_token import UserToken


async def save_user_token(db: AsyncSession, user_id: int, token: str, expires_at: datetime) -> UserToken:
    """保存用户令牌到数据库"""
    user_token = UserToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(user_token)
    await db.commit()
    await db.refresh(user_token)
    return user_token


async def get_valid_token(db: AsyncSession, token: str) -> Optional[UserToken]:
    """获取有效令牌（存在且未过期）"""
    now = datetime.utcnow()
    stmt = select(UserToken).where(
        and_(
            UserToken.token == token,
            UserToken.expires_at > now
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_user_token(db: AsyncSession, token: str) -> bool:
    """删除用户令牌（退出登录）"""
    stmt = delete(UserToken).where(UserToken.token == token)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def delete_user_tokens_by_user_id(db: AsyncSession, user_id: int) -> int:
    """删除用户所有令牌（用于强制下线等）"""
    stmt = delete(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


# 可选：清理过期令牌（定时任务）
async def clean_expired_tokens(db: AsyncSession) -> int:
    """删除所有过期的令牌"""
    now = datetime.utcnow()
    stmt = delete(UserToken).where(UserToken.expires_at <= now)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount