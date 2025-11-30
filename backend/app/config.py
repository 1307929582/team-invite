# 配置管理
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "ChatGPT Team Manager"
    APP_VERSION: str = "1.1.4"
    DEBUG: bool = False
    
    # GitHub 仓库（用于版本检查）
    GITHUB_REPO: str = "1307929582/team-invite"
    
    # API 配置
    API_PREFIX: str = "/api/v1"
    
    # ChatGPT API
    CHATGPT_API_BASE: str = "https://chat.openai.com/backend-api"
    
    # 数据库配置
    # 支持 SQLite 和 PostgreSQL
    # SQLite: sqlite:///./data/app.db
    # PostgreSQL: postgresql://user:password@localhost:5432/dbname
    DATABASE_URL: str = "sqlite:///./data/app.db"
    
    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Rate Limit
    INVITE_DELAY_SECONDS: float = 1.0
    MAX_BATCH_SIZE: int = 100
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    # LinuxDO OAuth 配置
    LINUXDO_CLIENT_ID: str = ""
    LINUXDO_CLIENT_SECRET: str = ""
    LINUXDO_REDIRECT_URI: str = "http://localhost:5173/auth/callback"
    LINUXDO_AUTH_URL: str = "https://connect.linux.do/oauth2/authorize"
    LINUXDO_TOKEN_URL: str = "https://connect.linux.do/oauth2/token"
    LINUXDO_USER_URL: str = "https://connect.linux.do/api/user"
    
    @property
    def is_sqlite(self) -> bool:
        """判断是否使用 SQLite"""
        return self.DATABASE_URL.startswith("sqlite")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
