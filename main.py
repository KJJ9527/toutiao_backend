from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from crud.user_token import clean_expired_tokens
from database import AsyncSessionLocal

from routers import news, favorite, user, history
from schemas.common import ApiResponse

from contextlib import asynccontextmanager
from utils.cache import init_redis, close_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    await init_redis()
    print("Redis connected")
    yield
    # 关闭时
    await close_redis()
    print("Redis closed")
app = FastAPI(lifespan=lifespan)

@app.on_event("startup")
async def startup_event():
    async with AsyncSessionLocal() as db:
        cleaned = await clean_expired_tokens(db)
        print(f"清理了 {cleaned} 条过期令牌")

# 自定义 HTTPException 处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(
            code=exc.status_code,
            message=exc.detail,
            data=None
        ).model_dump()
    )

# 自定义 ValidationError 处理器（FastAPI 表单/参数校验）
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ApiResponse(
            code=422,
            message="参数校验失败",
            data=exc.errors()  # 可返回详细错误信息
        ).model_dump()
    )

# 兜底异常处理器（捕获所有未预期的异常）
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content=ApiResponse(
            code=500,
            message=f"服务器内部错误: {str(exc)}",
            data=None
        ).model_dump()
    )



# ========== CORS 配置 ==========
origins = [
    "http://localhost",          # 本地默认
    "http://localhost:3000",     # React / Vue 开发服务器常见端口
    "http://localhost:5173",     # Vite 开发服务器
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    # 如果有其他前端地址，请添加到列表中
    # 例如：你的前端部署在某个域名或IP
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,               # 允许的源
    allow_credentials=True,              # 允许携带 Cookie
    allow_methods=["*"],                 # 允许所有 HTTP 方法（GET, POST, PUT, DELETE 等）
    allow_headers=["*"],                 # 允许所有请求头
)
# 注册路由
app.include_router(news.router)
app.include_router(favorite.router)
app.include_router(user.router)
app.include_router(history.router)




