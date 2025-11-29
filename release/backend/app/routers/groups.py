# Team 分组管理
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.models import TeamGroup, Team, RedeemCode, TeamMember, InviteRecord, InviteStatus
from app.services.auth import get_current_user

router = APIRouter(prefix="/groups", tags=["分组管理"])


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#1890ff"


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: str
    team_count: int = 0
    total_seats: int = 0
    used_seats: int = 0
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[GroupResponse])
async def list_groups(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """获取所有分组"""
    groups = db.query(TeamGroup).all()
    result = []
    
    for group in groups:
        # 统计该分组下的 Team 数量和座位
        teams = db.query(Team).filter(Team.group_id == group.id, Team.is_active == True).all()
        total_seats = sum(t.max_seats for t in teams)
        used_seats = 0
        for t in teams:
            member_count = db.query(TeamMember).filter(TeamMember.team_id == t.id).count()
            pending_count = db.query(InviteRecord).filter(
                InviteRecord.team_id == t.id,
                InviteRecord.status == InviteStatus.SUCCESS,
                InviteRecord.accepted_at == None
            ).count()
            used_seats += member_count + pending_count
        
        result.append(GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            color=group.color or "#1890ff",
            team_count=len(teams),
            total_seats=total_seats,
            used_seats=used_seats
        ))
    
    return result


@router.post("", response_model=GroupResponse)
async def create_group(data: GroupCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    """创建分组"""
    # 检查名称是否重复
    existing = db.query(TeamGroup).filter(TeamGroup.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="分组名称已存在")
    
    group = TeamGroup(
        name=data.name,
        description=data.description,
        color=data.color
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        color=group.color or "#1890ff",
        team_count=0,
        total_seats=0,
        used_seats=0
    )


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(group_id: int, data: GroupUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    """更新分组"""
    group = db.query(TeamGroup).filter(TeamGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    
    if data.name and data.name != group.name:
        existing = db.query(TeamGroup).filter(TeamGroup.name == data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="分组名称已存在")
        group.name = data.name
    
    if data.description is not None:
        group.description = data.description
    if data.color:
        group.color = data.color
    
    db.commit()
    db.refresh(group)
    
    # 统计
    teams = db.query(Team).filter(Team.group_id == group.id, Team.is_active == True).all()
    total_seats = sum(t.max_seats for t in teams)
    used_seats = sum(
        db.query(TeamMember).filter(TeamMember.team_id == t.id).count()
        for t in teams
    )
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        color=group.color or "#1890ff",
        team_count=len(teams),
        total_seats=total_seats,
        used_seats=used_seats
    )


@router.delete("/{group_id}")
async def delete_group(group_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    """删除分组"""
    group = db.query(TeamGroup).filter(TeamGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    
    # 检查是否有 Team 使用此分组
    team_count = db.query(Team).filter(Team.group_id == group_id).count()
    if team_count > 0:
        raise HTTPException(status_code=400, detail=f"该分组下还有 {team_count} 个 Team，无法删除")
    
    db.delete(group)
    db.commit()
    
    return {"message": "删除成功"}
