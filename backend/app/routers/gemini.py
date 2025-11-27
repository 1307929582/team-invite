# Gemini Business 管理 API
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models import GeminiTeam, GeminiMember, GeminiInviteRecord, User
from app.services.gemini_api import GeminiAPI, GeminiAPIError
from app.services.auth import get_current_user
from app.logger import get_logger

router = APIRouter(prefix="/gemini", tags=["gemini"])
logger = get_logger(__name__)


# ========== Schemas ==========
class GeminiTeamCreate(BaseModel):
    name: str
    description: Optional[str] = None
    account_id: str
    cookies: str
    max_seats: int = 10


class GeminiTeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cookies: Optional[str] = None
    max_seats: Optional[int] = None
    is_active: Optional[bool] = None


class GeminiTeamResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    account_id: str
    max_seats: int
    member_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GeminiMemberResponse(BaseModel):
    id: int
    email: str
    role: str
    gemini_member_id: Optional[int]
    synced_at: datetime

    class Config:
        from_attributes = True


class GeminiInviteRequest(BaseModel):
    emails: List[EmailStr]
    role: str = "viewer"


class GeminiInviteResponse(BaseModel):
    success: List[str]
    failed: List[dict]


class GeminiRemoveRequest(BaseModel):
    email: EmailStr


# ========== Team 管理 ==========
@router.get("/teams", response_model=List[GeminiTeamResponse])
async def list_gemini_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有 Gemini Team"""
    teams = db.query(GeminiTeam).all()
    
    result = []
    for team in teams:
        member_count = db.query(GeminiMember).filter(GeminiMember.team_id == team.id).count()
        result.append(GeminiTeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            account_id=team.account_id,
            max_seats=team.max_seats,
            member_count=member_count,
            is_active=team.is_active,
            created_at=team.created_at,
            updated_at=team.updated_at
        ))
    
    return result


@router.post("/teams", response_model=GeminiTeamResponse)
async def create_gemini_team(
    data: GeminiTeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建 Gemini Team"""
    # 测试连接
    api = GeminiAPI(data.account_id, data.cookies)
    test_result = await api.test_connection()
    
    if not test_result.get("success"):
        raise HTTPException(status_code=400, detail=f"连接测试失败: {test_result.get('error')}")
    
    team = GeminiTeam(
        name=data.name,
        description=data.description,
        account_id=data.account_id,
        cookies=data.cookies,
        max_seats=data.max_seats
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    
    # 同步成员
    await sync_team_members(team, db)
    
    member_count = db.query(GeminiMember).filter(GeminiMember.team_id == team.id).count()
    
    return GeminiTeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        account_id=team.account_id,
        max_seats=team.max_seats,
        member_count=member_count,
        is_active=team.is_active,
        created_at=team.created_at,
        updated_at=team.updated_at
    )


@router.get("/teams/{team_id}", response_model=GeminiTeamResponse)
async def get_gemini_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个 Gemini Team"""
    team = db.query(GeminiTeam).filter(GeminiTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    member_count = db.query(GeminiMember).filter(GeminiMember.team_id == team.id).count()
    
    return GeminiTeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        account_id=team.account_id,
        max_seats=team.max_seats,
        member_count=member_count,
        is_active=team.is_active,
        created_at=team.created_at,
        updated_at=team.updated_at
    )


@router.put("/teams/{team_id}", response_model=GeminiTeamResponse)
async def update_gemini_team(
    team_id: int,
    data: GeminiTeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新 Gemini Team"""
    team = db.query(GeminiTeam).filter(GeminiTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    if data.name is not None:
        team.name = data.name
    if data.description is not None:
        team.description = data.description
    if data.cookies is not None:
        team.cookies = data.cookies
    if data.max_seats is not None:
        team.max_seats = data.max_seats
    if data.is_active is not None:
        team.is_active = data.is_active
    
    team.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(team)
    
    member_count = db.query(GeminiMember).filter(GeminiMember.team_id == team.id).count()
    
    return GeminiTeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        account_id=team.account_id,
        max_seats=team.max_seats,
        member_count=member_count,
        is_active=team.is_active,
        created_at=team.created_at,
        updated_at=team.updated_at
    )


@router.delete("/teams/{team_id}")
async def delete_gemini_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除 Gemini Team"""
    team = db.query(GeminiTeam).filter(GeminiTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    db.delete(team)
    db.commit()
    
    return {"message": "删除成功"}


# ========== 成员管理 ==========
async def sync_team_members(team: GeminiTeam, db: Session):
    """同步 Team 成员"""
    try:
        api = GeminiAPI(team.account_id, team.cookies)
        members = await api.get_members()
        
        # 清除旧数据
        db.query(GeminiMember).filter(GeminiMember.team_id == team.id).delete()
        
        # 插入新数据
        for m in members:
            member = GeminiMember(
                team_id=team.id,
                email=m.get("email", ""),
                role=m.get("role", "viewer"),
                gemini_member_id=m.get("member_id"),
                synced_at=datetime.utcnow()
            )
            db.add(member)
        
        db.commit()
        logger.info(f"Gemini team sync completed", extra={
            "team": team.name,
            "member_count": len(members)
        })
    except Exception as e:
        logger.error(f"Gemini team sync failed", extra={
            "team": team.name,
            "error": str(e)
        })


@router.get("/teams/{team_id}/members", response_model=List[GeminiMemberResponse])
async def get_gemini_members(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 Team 成员列表"""
    team = db.query(GeminiTeam).filter(GeminiTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    members = db.query(GeminiMember).filter(GeminiMember.team_id == team_id).all()
    return members


@router.post("/teams/{team_id}/sync")
async def sync_gemini_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动同步 Team 成员"""
    team = db.query(GeminiTeam).filter(GeminiTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    await sync_team_members(team, db)
    
    member_count = db.query(GeminiMember).filter(GeminiMember.team_id == team.id).count()
    return {"message": "同步完成", "member_count": member_count}


@router.post("/teams/{team_id}/invite", response_model=GeminiInviteResponse)
async def invite_gemini_members(
    team_id: int,
    data: GeminiInviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """邀请成员加入 Gemini Team"""
    team = db.query(GeminiTeam).filter(GeminiTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    if not team.is_active:
        raise HTTPException(status_code=400, detail="Team 已禁用")
    
    api = GeminiAPI(team.account_id, team.cookies)
    result = await api.invite_members(data.emails, data.role)
    
    # 记录邀请
    for email in result.get("success", []):
        record = GeminiInviteRecord(
            team_id=team.id,
            email=email,
            role=data.role,
            status="success",
            invited_by=current_user.id
        )
        db.add(record)
    
    for item in result.get("failed", []):
        record = GeminiInviteRecord(
            team_id=team.id,
            email=item.get("email"),
            role=data.role,
            status="failed",
            error_message=item.get("error"),
            invited_by=current_user.id
        )
        db.add(record)
    
    db.commit()
    
    # 同步成员
    await sync_team_members(team, db)
    
    return GeminiInviteResponse(
        success=result.get("success", []),
        failed=result.get("failed", [])
    )


@router.post("/teams/{team_id}/remove")
async def remove_gemini_member(
    team_id: int,
    data: GeminiRemoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """移除 Gemini Team 成员"""
    team = db.query(GeminiTeam).filter(GeminiTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    api = GeminiAPI(team.account_id, team.cookies)
    
    try:
        await api.remove_member(data.email)
        
        # 同步成员
        await sync_team_members(team, db)
        
        return {"message": f"已移除 {data.email}"}
    except GeminiAPIError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/teams/{team_id}/test")
async def test_gemini_connection(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试 Gemini Team 连接"""
    team = db.query(GeminiTeam).filter(GeminiTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    api = GeminiAPI(team.account_id, team.cookies)
    result = await api.test_connection()
    
    return result


# ========== 邀请记录 ==========
@router.get("/teams/{team_id}/invites")
async def get_gemini_invites(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取邀请记录"""
    team = db.query(GeminiTeam).filter(GeminiTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    invites = db.query(GeminiInviteRecord).filter(
        GeminiInviteRecord.team_id == team_id
    ).order_by(GeminiInviteRecord.created_at.desc()).limit(100).all()
    
    return [{
        "id": i.id,
        "email": i.email,
        "role": i.role,
        "status": i.status.value,
        "error_message": i.error_message,
        "created_at": i.created_at.isoformat()
    } for i in invites]
