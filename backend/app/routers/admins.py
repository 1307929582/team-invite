# 管理员管理路由
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from app.database import get_db
from app.models import User, UserRole
from app.services.auth import get_current_user, get_password_hash

router = APIRouter(prefix="/admins", tags=["管理员管理"])


class AdminResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class AdminCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "admin"


class AdminUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("", response_model=List[AdminResponse])
async def list_admins(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有管理员列表"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有管理员可以查看")
    
    users = db.query(User).filter(User.role.in_([UserRole.ADMIN, UserRole.OPERATOR])).all()
    return [AdminResponse(
        id=u.id,
        username=u.username,
        email=u.email,
        role=u.role.value,
        is_active=u.is_active,
        created_at=u.created_at.isoformat() if u.created_at else ""
    ) for u in users]


@router.post("", response_model=AdminResponse)
async def create_admin(
    data: AdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新管理员"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有管理员可以创建")
    
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    # 验证角色
    try:
        role = UserRole(data.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的角色")
    
    user = User(
        username=data.username.strip(),
        email=data.email.lower().strip(),
        hashed_password=get_password_hash(data.password),
        role=role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return AdminResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else ""
    )


@router.put("/{admin_id}", response_model=AdminResponse)
async def update_admin(
    admin_id: int,
    data: AdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新管理员信息"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有管理员可以修改")
    
    user = db.query(User).filter(User.id == admin_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if data.email:
        existing = db.query(User).filter(User.email == data.email, User.id != admin_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        user.email = data.email.lower().strip()
    
    if data.password:
        user.hashed_password = get_password_hash(data.password)
    
    if data.role:
        try:
            user.role = UserRole(data.role)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的角色")
    
    if data.is_active is not None:
        # 不能禁用自己
        if admin_id == current_user.id and not data.is_active:
            raise HTTPException(status_code=400, detail="不能禁用自己")
        user.is_active = data.is_active
    
    db.commit()
    db.refresh(user)
    
    return AdminResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else ""
    )


@router.delete("/{admin_id}")
async def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除管理员"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有管理员可以删除")
    
    if admin_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    user = db.query(User).filter(User.id == admin_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    db.delete(user)
    db.commit()
    
    return {"message": "删除成功"}
