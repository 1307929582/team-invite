# 兑换码管理 API
from datetime import datetime, timedelta
from typing import Optional, List
import secrets
import string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import RedeemCode, RedeemCodeType, User, TeamGroup, InviteRecord
from app.services.auth import get_current_user

router = APIRouter(prefix="/redeem-codes", tags=["redeem-codes"])


class RedeemCodeCreate(BaseModel):
    max_uses: int = 1
    expires_days: Optional[int] = None
    count: int = 1
    prefix: str = ""
    code_type: str = "linuxdo"  # linuxdo 或 direct
    note: Optional[str] = None
    group_id: Optional[int] = None  # 绑定分组


class RedeemCodeResponse(BaseModel):
    id: int
    code: str
    code_type: str
    max_uses: int
    used_count: int
    expires_at: Optional[datetime]
    is_active: bool
    note: Optional[str]
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RedeemCodeListResponse(BaseModel):
    codes: List[RedeemCodeResponse]
    total: int


class BatchCreateResponse(BaseModel):
    codes: List[str]
    count: int


def generate_code(prefix: str = "", length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(chars) for _ in range(length))
    return f"{prefix}{code}" if prefix else code


@router.get("", response_model=RedeemCodeListResponse)
async def list_redeem_codes(
    is_active: Optional[bool] = None,
    code_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取兑换码列表"""
    query = db.query(RedeemCode)
    
    if is_active is not None:
        query = query.filter(RedeemCode.is_active == is_active)
    
    if code_type:
        query = query.filter(RedeemCode.code_type == code_type)
    
    codes = query.order_by(RedeemCode.created_at.desc()).all()
    
    # 获取分组名称映射
    group_ids = [c.group_id for c in codes if c.group_id]
    groups = {}
    if group_ids:
        group_list = db.query(TeamGroup).filter(TeamGroup.id.in_(group_ids)).all()
        groups = {g.id: g.name for g in group_list}
    
    return RedeemCodeListResponse(
        codes=[RedeemCodeResponse(
            id=c.id,
            code=c.code,
            code_type=c.code_type.value if c.code_type else "linuxdo",
            max_uses=c.max_uses,
            used_count=c.used_count,
            expires_at=c.expires_at,
            is_active=c.is_active,
            note=c.note,
            group_id=c.group_id,
            group_name=groups.get(c.group_id) if c.group_id else None,
            created_at=c.created_at
        ) for c in codes],
        total=len(codes)
    )


@router.post("/batch", response_model=BatchCreateResponse)
async def batch_create_codes(
    data: RedeemCodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量创建兑换码"""
    if data.count < 1 or data.count > 100:
        raise HTTPException(status_code=400, detail="数量必须在 1-100 之间")
    
    expires_at = None
    if data.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=data.expires_days)
    
    # 确定兑换码类型
    code_type = RedeemCodeType.DIRECT if data.code_type == "direct" else RedeemCodeType.LINUXDO
    
    codes = []
    for _ in range(data.count):
        while True:
            code_str = generate_code(data.prefix)
            existing = db.query(RedeemCode).filter(RedeemCode.code == code_str).first()
            if not existing:
                break
        
        code = RedeemCode(
            code=code_str,
            code_type=code_type,
            max_uses=data.max_uses,
            expires_at=expires_at,
            note=data.note,
            group_id=data.group_id,
            created_by=current_user.id
        )
        db.add(code)
        codes.append(code_str)
    
    db.commit()
    
    return BatchCreateResponse(codes=codes, count=len(codes))


@router.delete("/{code_id}")
async def delete_code(
    code_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除兑换码"""
    code = db.query(RedeemCode).filter(RedeemCode.id == code_id).first()
    if not code:
        raise HTTPException(status_code=404, detail="兑换码不存在")
    
    db.delete(code)
    db.commit()
    
    return {"message": "删除成功"}


@router.put("/{code_id}/toggle")
async def toggle_code(
    code_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """禁用/启用兑换码"""
    code = db.query(RedeemCode).filter(RedeemCode.id == code_id).first()
    if not code:
        raise HTTPException(status_code=404, detail="兑换码不存在")
    
    code.is_active = not code.is_active
    db.commit()
    
    return {"message": "已" + ("启用" if code.is_active else "禁用"), "is_active": code.is_active}



class InviteRecordResponse(BaseModel):
    id: int
    email: str
    team_name: str
    status: str
    created_at: datetime
    accepted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.get("/{code_id}/records")
async def get_code_records(
    code_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取兑换码使用记录"""
    code = db.query(RedeemCode).filter(RedeemCode.id == code_id).first()
    if not code:
        raise HTTPException(status_code=404, detail="兑换码不存在")
    
    from app.models import Team
    
    # 查询使用该兑换码的邀请记录
    records = db.query(InviteRecord).filter(
        InviteRecord.redeem_code == code.code
    ).order_by(InviteRecord.created_at.desc()).all()
    
    # 获取 Team 名称
    team_ids = [r.team_id for r in records]
    teams = {}
    if team_ids:
        team_list = db.query(Team).filter(Team.id.in_(team_ids)).all()
        teams = {t.id: t.name for t in team_list}
    
    return {
        "code": code.code,
        "records": [
            InviteRecordResponse(
                id=r.id,
                email=r.email,
                team_name=teams.get(r.team_id, "未知"),
                status=r.status.value,
                created_at=r.created_at,
                accepted_at=r.accepted_at
            )
            for r in records
        ]
    }
