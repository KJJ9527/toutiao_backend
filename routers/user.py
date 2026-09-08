# routers/user.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta          # 补上这两个导入

from database import get_db
from crud.user import (
    get_user_by_username, create_user,
    get_user_by_id, update_user_info, update_password
)
from crud.user_token import save_user_token, delete_user_token   # 补上这两个导入
from schemas.common import ApiResponse
from schemas.user import (
    RegisterRequest, LoginRequest, UserInfo,
    LoginResponseData, UpdateUserRequest, ChangePasswordRequest
)
from utils.auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user
)
from config.db_conf import db_settings   # 获取 JWT 过期时间配置

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.post("/register", response_model=ApiResponse)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    # 检查用户名是否已存在
    existing = await get_user_by_username(db, req.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 加密密码并创建用户
    hashed_password = get_password_hash(req.password)
    user = await create_user(db, req.username, hashed_password)

    # 生成 Token
    token = create_access_token(data={"sub": str(user.id)})

    # 保存 token 到 user_token 表（使用配置中的过期时间）
    expires_delta = timedelta(minutes=db_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expires_at = datetime.utcnow() + expires_delta
    await save_user_token(db, user.id, token, expires_at)

    # 构造返回数据
    user_info = UserInfo(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        avatar=user.avatar or "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
        gender=user.gender,
        bio=user.bio or "这个人很懒，什么都没留下"
    )
    response_data = LoginResponseData(token=token, userInfo=user_info)
    return ApiResponse(message="注册成功", data=response_data.model_dump())


@router.post("/login", response_model=ApiResponse)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    # 验证用户
    user = await get_user_by_username(db, req.username)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 生成 Token
    token = create_access_token(data={"sub": str(user.id)})

    # 保存 token 到 user_token 表
    expires_delta = timedelta(minutes=db_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expires_at = datetime.utcnow() + expires_delta
    await save_user_token(db, user.id, token, expires_at)

    # 构造返回数据
    user_info = UserInfo(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        avatar=user.avatar or "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
        gender=user.gender,
        bio=user.bio or "这个人很懒，什么都没留下"
    )
    response_data = LoginResponseData(token=token, userInfo=user_info)
    return ApiResponse(message="登录成功", data=response_data.model_dump())


@router.post("/logout", response_model=ApiResponse)
async def logout(
    request: Request,
    current_user = Depends(get_current_user),   # 先验证 token 有效性
    db: AsyncSession = Depends(get_db)
):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供令牌")
    token = auth_header.split(" ")[1]

    deleted = await delete_user_token(db, token)
    if not deleted:
        raise HTTPException(status_code=404, detail="令牌不存在或已过期")

    return ApiResponse(message="退出成功", data=None)


@router.get("/info", response_model=ApiResponse)
async def get_user_info(
    current_user = Depends(get_current_user)
):
    user_info = UserInfo(
        id=current_user.id,
        username=current_user.username,
        nickname=current_user.nickname,
        avatar=current_user.avatar or "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
        gender=current_user.gender,
        bio=current_user.bio or "这个人很懒，什么都没留下"
    )
    return ApiResponse(data=user_info.model_dump())


@router.put("/update", response_model=ApiResponse)
async def update_user(
    req: UpdateUserRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated_user = await update_user_info(db, current_user.id, req)
    user_info = UserInfo(
        id=updated_user.id,
        username=updated_user.username,
        nickname=updated_user.nickname,
        avatar=updated_user.avatar or "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
        gender=updated_user.gender,
        bio=updated_user.bio or "这个人很懒，什么都没留下"
    )
    return ApiResponse(message="更新成功", data=user_info.model_dump())


@router.put("/password", response_model=ApiResponse)
async def change_password(
        req: ChangePasswordRequest,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    # 验证旧密码
    if not verify_password(req.oldPassword, current_user.password):
        raise HTTPException(status_code=400, detail="当前密码错误")

    # 验证新旧密码是否相同
    if req.newPassword == req.oldPassword:
        raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")

    # 加密新密码并更新
    new_hashed = get_password_hash(req.newPassword)
    success = await update_password(db, current_user.id, new_hashed)
    if not success:
        raise HTTPException(status_code=500, detail="密码修改失败")

    # 删除该用户所有 token，强制重新登录
    from crud.user_token import delete_user_tokens_by_user_id
    await delete_user_tokens_by_user_id(db, current_user.id)

    # 返回成功，提示重新登录
    return ApiResponse(message="密码修改成功，请重新登录", data=None)