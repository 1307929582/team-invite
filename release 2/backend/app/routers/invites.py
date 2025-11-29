# 邀请管理路由
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Team, InviteRecord, OperationLog, User, InviteStatus
from app.schemas import (
    InviteRequest, BatchInviteResponse, InviteResult,
    InviteRecordResponse, MessageResponse
)
from app.services.auth import get_current_user
from app.services.chatgpt_api import ChatGPTAPI, batch_invite
from app.config import settings

router = APIRouter(prefix="/teams/{team_id}/invites", tags=["邀请管理"])


@router.post("", response_model=BatchInviteResponse)
async def invite_members(
    team_id: int,
    invite_data: InviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量邀请成员"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    if len(invite_data.emails) > settings.MAX_BATCH_SIZE:
        raise HTTPException(status_code=400, detail=f"单次最多邀请 {settings.MAX_BATCH_SIZE} 人")
    
    batch_id = str(uuid.uuid4())[:8]
    
    # 执行邀请
    api = ChatGPTAPI(team.session_token, team.device_id or "", team.cookie or "")
    results = await batch_invite(api, team.account_id, [str(e) for e in invite_data.emails])
    
    # 保存记录
    success_count = 0
    fail_count = 0
    
    for r in results:
        status = InviteStatus.SUCCESS if r["success"] else InviteStatus.FAILED
        if r["success"]:
            success_count += 1
        else:
            fail_count += 1
        
        record = InviteRecord(
            team_id=team_id,
            email=r["email"],
            status=status,
            error_message=r.get("error"),
            invited_by=current_user.id,
            batch_id=batch_id
        )
        db.add(record)
    
    # 记录操作日志
    log = OperationLog(
        user_id=current_user.id,
        team_id=team_id,
        action="batch_invite",
        target=f"{len(invite_data.emails)} 人",
        details=f"成功: {success_count}, 失败: {fail_count}, 批次: {batch_id}"
    )
    db.add(log)
    db.commit()
    
    return BatchInviteResponse(
        batch_id=batch_id,
        total=len(results),
        success_count=success_count,
        fail_count=fail_count,
        results=[InviteResult(**r) for r in results]
    )


@router.get("", response_model=List[InviteRecordResponse])
async def list_invite_records(
    team_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取邀请记录"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    records = db.query(InviteRecord).filter(
        InviteRecord.team_id == team_id
    ).order_by(InviteRecord.created_at.desc()).limit(limit).all()
    
    return [InviteRecordResponse.model_validate(r) for r in records]


@router.get("/pending")
async def get_pending_invites(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 ChatGPT 上待处理的邀请"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    try:
        api = ChatGPTAPI(team.session_token)
        result = await api.get_invites(team.account_id)
        invites = result.get("items", result.get("invites", []))
        return {"invites": invites, "total": len(invites)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
