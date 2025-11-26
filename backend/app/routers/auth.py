# 认证路由
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole, OperationLog
from app.schemas import Token, UserCreate, UserResponse, UserLogin
from app.services.auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash,
    get_current_user,
    get_current_admin
)
from app.config import settings
from app.limiter import limiter
from app.logger import get_logger

router = APIRouter(prefix="/auth", tags=["认证"])
logger = get_logger(__name__)


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # 每分钟最多5次登录尝试
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning("Login failed", extra={
            "username": form_data.username,
            "client_ip": request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    logger.info("Login success", extra={"username": user.username, "client_ip": client_ip})
    
    # 记录登录日志
    log = OperationLog(
        user_id=user.id,
        action="登录",
        target=user.username,
        details=f"IP: {client_ip}",
        ip_address=client_ip
    )
    db.add(log)
    db.commit()
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """注册新用户（仅管理员）"""
    # 检查用户名是否存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    # 创建用户
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


# 已移除 init-admin 接口，改用 /setup/initialize
