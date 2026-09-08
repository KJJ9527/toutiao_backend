# schemas/user.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# 注册请求
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=50)

# 登录请求
class LoginRequest(BaseModel):
    username: str
    password: str

# 用户信息响应
class UserInfo(BaseModel):
    id: int
    username: str
    nickname: Optional[str] = None
    avatar: str = "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"  # 默认头像
    gender: str = "unknown"
    bio: Optional[str] = "这个人很懒，什么都没留下"

    class Config:
        from_attributes = True

# 登录/注册响应数据
class LoginResponseData(BaseModel):
    token: str
    userInfo: UserInfo

# 更新用户信息请求
class UpdateUserRequest(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None

# 修改密码请求
class ChangePasswordRequest(BaseModel):
    oldPassword: str
    newPassword: str

