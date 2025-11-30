# 数据库连接
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import Base
import os

# SQLite 需要确保数据目录存在
if settings.is_sqlite:
    os.makedirs("data", exist_ok=True)

# 根据数据库类型配置引擎
if settings.is_sqlite:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}  # SQLite 需要
    )
else:
    # PostgreSQL / MySQL 等
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,          # 增加连接池大小
        max_overflow=40,       # 增加溢出连接数
        pool_pre_ping=True,    # 连接前检测
        pool_recycle=300,      # 5分钟回收连接
        pool_timeout=30,       # 连接超时30秒
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库表（跳过已存在的）"""
    from sqlalchemy import inspect
    inspector = inspect(engine)
    
    # 只创建不存在的表
    Base.metadata.create_all(bind=engine, checkfirst=True)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
