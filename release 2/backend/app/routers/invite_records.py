# 邀请记录管理 API
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import InviteRecord, Team, TeamGroup, LinuxDOUser, User
from app.services.auth import get_current_user

router = APIRouter(prefix="/invite-records", tags=["invite-records"])


class InviteRecordResponse(BaseModel):
    id: int
    email: str
    team_id: int
    team_name: str
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    group_color: Optional[str] = None
    status: str
    redeem_code: Optional[str] = None
    linuxdo_username: Optional[str] = None
    created_at: datetime
    accepted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InviteRecordListResponse(BaseModel):
    records: List[InviteRecordResponse]
    total: int


@router.get("", response_model=InviteRecordListResponse)
async def list_invite_records(
    search: Optional[str] = None,
    team_id: Optional[int] = None,
    group_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取邀请记录列表"""
    query = db.query(InviteRecord)
    
    if team_id:
        query = query.filter(InviteRecord.team_id == team_id)
    
    if search:
        query = query.filter(
            (InviteRecord.email.contains(search)) |
            (InviteRecord.redeem_code.contains(search))
        )
    
    records = query.order_by(InviteRecord.created_at.desc()).all()
    
    # 获取 Team 信息
    team_ids = list(set([r.team_id for r in records]))
    teams = {}
    team_group_map = {}
    if team_ids:
        team_list = db.query(Team).filter(Team.id.in_(team_ids)).all()
        teams = {t.id: t.name for t in team_list}
        team_group_map = {t.id: t.group_id for t in team_list}
    
    # 获取分组信息
    group_ids = list(set([gid for gid in team_group_map.values() if gid]))
    groups = {}
    if group_ids:
        group_list = db.query(TeamGroup).filter(TeamGroup.id.in_(group_ids)).all()
        groups = {g.id: {"name": g.name, "color": g.color} for g in group_list}
    
    # 获取 LinuxDO 用户信息
    linuxdo_user_ids = list(set([r.linuxdo_user_id for r in records if r.linuxdo_user_id]))
    linuxdo_users = {}
    if linuxdo_user_ids:
        user_list = db.query(LinuxDOUser).filter(LinuxDOUser.id.in_(linuxdo_user_ids)).all()
        linuxdo_users = {u.id: u.username for u in user_list}
    
    # 按分组筛选
    result = []
    for r in records:
        team_gid = team_group_map.get(r.team_id)
        if group_id and team_gid != group_id:
            continue
        
        group_info = groups.get(team_gid, {}) if team_gid else {}
        
        result.append(InviteRecordResponse(
            id=r.id,
            email=r.email,
            team_id=r.team_id,
            team_name=teams.get(r.team_id, "未知"),
            group_id=team_gid,
            group_name=group_info.get("name"),
            group_color=group_info.get("color"),
            status=r.status.value,
            redeem_code=r.redeem_code,
            linuxdo_username=linuxdo_users.get(r.linuxdo_user_id) if r.linuxdo_user_id else None,
            created_at=r.created_at,
            accepted_at=r.accepted_at
        ))
    
    return InviteRecordListResponse(records=result, total=len(result))
