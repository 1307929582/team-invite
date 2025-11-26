# Dashboard 路由
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.database import get_db
from app.models import Team, TeamMember, InviteRecord, OperationLog, User, InviteStatus
from app.schemas import DashboardStats, OperationLogResponse, OperationLogListResponse
from app.services.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class TeamSeatInfo(BaseModel):
    id: int
    name: str
    max_seats: int
    used_seats: int
    pending_seats: int
    available_seats: int


class SeatStatsResponse(BaseModel):
    total_seats: int
    used_seats: int
    pending_seats: int
    available_seats: int
    teams: List[TeamSeatInfo]


@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 Dashboard 统计数据"""
    # 总 Team 数
    total_teams = db.query(Team).filter(Team.is_active == True).count()
    
    # 活跃 Team 数（有成员的）
    active_teams = db.query(Team).join(TeamMember).filter(Team.is_active == True).distinct().count()
    
    # 总成员数
    total_members = db.query(TeamMember).count()
    
    # 今日邀请数
    today = datetime.utcnow().date()
    invites_today = db.query(InviteRecord).filter(
        func.date(InviteRecord.created_at) == today
    ).count()
    
    # 本周邀请数
    week_ago = datetime.utcnow() - timedelta(days=7)
    invites_this_week = db.query(InviteRecord).filter(
        InviteRecord.created_at >= week_ago
    ).count()
    
    # 近7天邀请趋势
    invite_trend = []
    for i in range(6, -1, -1):
        date = (datetime.utcnow() - timedelta(days=i)).date()
        count = db.query(InviteRecord).filter(
            func.date(InviteRecord.created_at) == date
        ).count()
        invite_trend.append({"date": date.isoformat(), "count": count})
    
    return {
        "total_teams": total_teams,
        "total_members": total_members,
        "invites_today": invites_today,
        "invites_this_week": invites_this_week,
        "active_teams": active_teams,
        "invite_trend": invite_trend
    }


@router.get("/seats", response_model=SeatStatsResponse)
async def get_seat_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取座位统计（管理员）"""
    teams = db.query(Team).filter(Team.is_active == True).all()
    
    total_seats = 0
    total_used = 0
    total_pending = 0
    team_infos = []
    
    for team in teams:
        max_seats = team.max_seats
        total_seats += max_seats
        
        # 已同步成员
        used = db.query(TeamMember).filter(TeamMember.team_id == team.id).count()
        total_used += used
        
        # 已邀请未接受
        pending = db.query(InviteRecord).filter(
            InviteRecord.team_id == team.id,
            InviteRecord.status == InviteStatus.SUCCESS,
            InviteRecord.accepted_at == None
        ).count()
        total_pending += pending
        
        available = max_seats - used - pending
        if available < 0:
            available = 0
        
        team_infos.append(TeamSeatInfo(
            id=team.id,
            name=team.name,
            max_seats=max_seats,
            used_seats=used,
            pending_seats=pending,
            available_seats=available
        ))
    
    total_available = total_seats - total_used - total_pending
    if total_available < 0:
        total_available = 0
    
    return SeatStatsResponse(
        total_seats=total_seats,
        used_seats=total_used,
        pending_seats=total_pending,
        available_seats=total_available,
        teams=team_infos
    )


@router.get("/logs", response_model=OperationLogListResponse)
async def get_operation_logs(
    limit: int = 50,
    team_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取操作日志"""
    query = db.query(OperationLog)
    
    if team_id:
        query = query.filter(OperationLog.team_id == team_id)
    
    logs = query.order_by(OperationLog.created_at.desc()).limit(limit).all()
    
    result = []
    for log in logs:
        log_dict = OperationLogResponse.model_validate(log).model_dump()
        # 添加用户名和 Team 名
        if log.user:
            log_dict["user_name"] = log.user.username
        if log.team:
            log_dict["team_name"] = log.team.name
        result.append(OperationLogResponse(**log_dict))
    
    total = query.count()
    return OperationLogListResponse(logs=result, total=total)
