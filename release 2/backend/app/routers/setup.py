# 初始化设置 API
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import secrets

from app.database import get_db
from app.models import User, UserRole, SystemConfig
from app.services.auth import get_password_hash

router = APIRouter(prefix="/setup", tags=["setup"])


class SetupStatus(BaseModel):
    initialized: bool
    has_admin: bool


class SetupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str


class SetupResponse(BaseModel):
    success: bool
    message: str


def is_system_initialized(db: Session) -> bool:
    """检查系统是否已初始化"""
    # 检查是否有管理员用户
    admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
    return admin_count > 0


@router.get("/status", response_model=SetupStatus)
async def get_setup_status(db: Session = Depends(get_db)):
    """获取系统初始化状态（公开接口）"""
    initialized = is_system_initialized(db)
    return SetupStatus(
        initialized=initialized,
        has_admin=initialized
    )


@router.post("/initialize", response_model=SetupResponse)
async def initialize_system(data: SetupRequest, db: Session = Depends(get_db)):
    """初始化系统，创建管理员账号（仅在未初始化时可用）"""
    # 检查是否已初始化
    if is_system_initialized(db):
        raise HTTPException(
            status_code=403, 
            detail="系统已初始化，无法重复设置"
        )
    
    # 验证密码
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少6位")
    
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="两次密码不一致")
    
    # 验证用户名
    if len(data.username) < 3:
        raise HTTPException(status_code=400, detail="用户名长度至少3位")
    
    # 创建管理员用户
    admin = User(
        username=data.username.strip(),
        email=data.email.lower().strip(),
        hashed_password=get_password_hash(data.password),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin)
    
    # 生成随机 SECRET_KEY 并保存到配置
    secret_key = secrets.token_urlsafe(32)
    config = SystemConfig(
        key="jwt_secret_key",
        value=secret_key,
        description="JWT 签名密钥（自动生成）"
    )
    db.add(config)
    
    # 标记系统已初始化
    init_config = SystemConfig(
        key="system_initialized",
        value="true",
        description="系统初始化标记"
    )
    db.add(init_config)
    
    db.commit()
    
    return SetupResponse(
        success=True,
        message="系统初始化成功！请使用管理员账号登录"
    )
