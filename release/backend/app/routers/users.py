# LinuxDO 用户管理 API
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import LinuxDOUser, InviteRecord, Team, User
from app.services.auth import get_current_user

router = APIRouter(prefix="/linuxdo-users", tags=["linuxdo-users"])


class LinuxDOUserResponse(BaseModel):
    id: int
    linuxdo_id: str
    username: str
    name: Optional[str]
    email: Optional[str]
    trust_level: int
    avatar_url: Optional[str]
    created_at: datetime
    last_login: datetime
    # 邀请信息
    invite_email: Optional[str] = None
    invite_team: Optional[str] = None
    invite_status: Optional[str] = None
    invite_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class LinuxDOUserListResponse(BaseModel):
    users: List[LinuxDOUserResponse]
    total: int


@router.get("", response_model=LinuxDOUserListResponse)
async def list_linuxdo_users(
    search: Optional[str] = None,
    has_invite: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 LinuxDO 用户列表"""
    query = db.query(LinuxDOUser)
    
    if search:
        query = query.filter(
            (LinuxDOUser.username.contains(search)) |
            (LinuxDOUser.name.contains(search)) |
            (LinuxDOUser.linuxdo_id.contains(search))
        )
    
    users = query.order_by(LinuxDOUser.last_login.desc()).all()
    
    result = []
    for user in users:
        # 获取最新邀请记录
        invite = db.query(InviteRecord).filter(
            InviteRecord.linuxdo_user_id == user.id
        ).order_by(InviteRecord.created_at.desc()).first()
        
        if has_invite is not None:
            if has_invite and not invite:
                continue
            if not has_invite and invite:
                continue
        
        team_name = None
        if invite:
            team = db.query(Team).filter(Team.id == invite.team_id).first()
            team_name = team.name if team else None
        
        result.append(LinuxDOUserResponse(
            id=user.id,
            linuxdo_id=user.linuxdo_id,
            username=user.username,
            name=user.name,
            email=user.email,
            trust_level=user.trust_level,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
            last_login=user.last_login,
            invite_email=invite.email if invite else None,
            invite_team=team_name,
            invite_status=invite.status.value if invite else None,
            invite_time=invite.created_at if invite else None
        ))
    
    return LinuxDOUserListResponse(users=result, total=len(result))


@router.get("/{user_id}")
async def get_linuxdo_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个 LinuxDO 用户详情"""
    user = db.query(LinuxDOUser).filter(LinuxDOUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取所有邀请记录
    invites = db.query(InviteRecord).filter(
        InviteRecord.linuxdo_user_id == user.id
    ).order_by(InviteRecord.created_at.desc()).all()
    
    invite_records = []
    for invite in invites:
        team = db.query(Team).filter(Team.id == invite.team_id).first()
        invite_records.append({
            "id": invite.id,
            "email": invite.email,
            "team_name": team.name if team else None,
            "status": invite.status.value,
            "redeem_code": invite.redeem_code,
            "created_at": invite.created_at.isoformat(),
            "accepted_at": invite.accepted_at.isoformat() if invite.accepted_at else None
        })
    
    return {
        "id": user.id,
        "linuxdo_id": user.linuxdo_id,
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "trust_level": user.trust_level,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat(),
        "invites": invite_records
    }
