# config/db_conf.py
import os
from dotenv import load_dotenv

load_dotenv()

class DBSettings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+asyncmy://root:123456@localhost:3306/news_app?charset=utf8mb4"
    )
    # 连接池配置
    POOL_SIZE: int = 10
    MAX_OVERFLOW: int = 20
    POOL_RECYCLE: int = 3600

    # JWT 配置
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

db_settings = DBSettings()