# crud/user.py
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from models.user import User
from schemas.user import UpdateUserRequest

async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, username: str, hashed_password: str) -> User:
    user = User(username=username, password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def update_user_info(db: AsyncSession, user_id: int, update_data: UpdateUserRequest) -> User:
    # 构建更新字段
    values = {}
    if update_data.nickname is not None:
        values["nickname"] = update_data.nickname
    if update_data.avatar is not None:
        values["avatar"] = update_data.avatar
    if update_data.gender is not None:
        values["gender"] = update_data.gender
    if update_data.bio is not None:
        values["bio"] = update_data.bio
    if update_data.phone is not None:
        values["phone"] = update_data.phone
    if not values:
        # 没有更新项，直接返回当前用户
        return await get_user_by_id(db, user_id)
    stmt = update(User).where(User.id == user_id).values(**values).returning(User)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()

async def update_password(db: AsyncSession, user_id: int, new_hashed_password: str) -> bool:
    stmt = update(User).where(User.id == user_id).values(password=new_hashed_password)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0