# 公开 API（用户自助申请）
from datetime import datetime
import httpx
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.database import get_db
from app.models import (
    Team, TeamMember, RedeemCode, RedeemCodeType, LinuxDOUser, InviteRecord, InviteStatus, 
    SystemConfig, OperationLog
)
from app.services.chatgpt_api import ChatGPTAPI, ChatGPTAPIError
from app.services.telegram import notify_new_invite
from app.limiter import limiter
from app.logger import get_logger

router = APIRouter(prefix="/public", tags=["public"])
logger = get_logger(__name__)

# 全局并发控制：最多同时处理 10 个兑换请求
import asyncio
_redeem_semaphore = asyncio.Semaphore(10)


def get_config(db: Session, key: str) -> Optional[str]:
    """获取系统配置"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return config.value if config else None


async def send_invite_telegram_notify(db: Session, email: str, team_name: str, redeem_code: str, username: str = None):
    """发送邀请成功的 Telegram 通知"""
    try:
        tg_enabled = get_config(db, "telegram_enabled")
        notify_invite = get_config(db, "telegram_notify_invite")
        
        if tg_enabled != "true" or notify_invite != "true":
            return
        
        bot_token = get_config(db, "telegram_bot_token")
        chat_id = get_config(db, "telegram_chat_id")
        
        if bot_token and chat_id:
            await notify_new_invite(bot_token, chat_id, email, team_name, redeem_code, username)
    except Exception as e:
        logger.warning(f"Telegram notify failed: {e}")


# ========== 站点配置 ==========
class SiteConfig(BaseModel):
    site_title: str = "ChatGPT Team 自助上车"
    site_description: str = "使用兑换码加入 Team"
    home_notice: str = ""  # 首页公告
    success_message: str = "邀请已发送！请查收邮箱并接受邀请"
    footer_text: str = ""  # 页脚文字


@router.get("/site-config", response_model=SiteConfig)
async def get_site_config(db: Session = Depends(get_db)):
    """获取站点配置（公开，带缓存）"""
    from app.cache import get_site_config_cache, set_site_config_cache
    
    # 尝试从缓存获取
    cached = get_site_config_cache()
    if cached:
        return SiteConfig(**cached)
    
    # 从数据库获取
    result = SiteConfig(
        site_title=get_config(db, "site_title") or "ChatGPT Team 自助上车",
        site_description=get_config(db, "site_description") or "使用兑换码加入 Team",
        home_notice=get_config(db, "home_notice") or "",
        success_message=get_config(db, "success_message") or "邀请已发送！请查收邮箱并接受邀请",
        footer_text=get_config(db, "footer_text") or "",
    )
    
    # 写入缓存
    set_site_config_cache(result.model_dump())
    return result


def get_available_team(db: Session, group_id: Optional[int] = None, group_name: Optional[str] = None) -> Optional[Team]:
    """获取有空位的 Team（优化版，不锁表）
    
    使用子查询统计成员数，避免 N+1 查询和锁表
    """
    from sqlalchemy import func, and_
    
    team_query = db.query(Team).filter(Team.is_active == True)
    
    if group_id:
        team_query = team_query.filter(Team.group_id == group_id)
    elif group_name:
        from app.models import TeamGroup
        group = db.query(TeamGroup).filter(TeamGroup.name == group_name).first()
        if group:
            team_query = team_query.filter(Team.group_id == group.id)
        else:
            return None
    
    # 子查询统计每个 Team 的成员数
    member_count_subq = db.query(
        TeamMember.team_id,
        func.count(TeamMember.id).label('member_count')
    ).group_by(TeamMember.team_id).subquery()
    
    # 联合查询，找到有空位的 Team
    available_team = team_query.outerjoin(
        member_count_subq,
        Team.id == member_count_subq.c.team_id
    ).filter(
        func.coalesce(member_count_subq.c.member_count, 0) < Team.max_seats
    ).first()
    
    return available_team


# ========== Schemas ==========
class LinuxDOAuthURL(BaseModel):
    auth_url: str
    state: str


class LinuxDOCallback(BaseModel):
    code: str
    state: str


class LinuxDOUserInfo(BaseModel):
    id: int
    linuxdo_id: str
    username: str
    name: Optional[str]
    email: Optional[str]
    trust_level: int
    avatar_url: Optional[str]
    token: str


class RedeemRequest(BaseModel):
    email: EmailStr
    redeem_code: str
    linuxdo_token: str


class RedeemResponse(BaseModel):
    success: bool
    message: str
    team_name: Optional[str] = None


class UserStatusResponse(BaseModel):
    has_active_invite: bool
    team_name: Optional[str] = None
    invite_email: Optional[str] = None
    invite_status: Optional[str] = None
    invite_time: Optional[str] = None


# ========== LinuxDO OAuth ==========
@router.get("/linuxdo/auth")
async def get_linuxdo_auth_url(db: Session = Depends(get_db)):
    """获取 LinuxDO OAuth 授权 URL（带缓存）"""
    from app.cache import get_linuxdo_auth_cache, set_linuxdo_auth_cache
    
    # 尝试从缓存获取配置
    cached = get_linuxdo_auth_cache()
    if cached:
        client_id = cached.get("client_id")
        redirect_uri = cached.get("redirect_uri")
    else:
        client_id = get_config(db, "linuxdo_client_id")
        redirect_uri = get_config(db, "linuxdo_redirect_uri")
        if client_id:
            set_linuxdo_auth_cache({"client_id": client_id, "redirect_uri": redirect_uri})
    
    if not client_id:
        raise HTTPException(status_code=500, detail="LinuxDO OAuth 未配置，请联系管理员")
    
    state = secrets.token_urlsafe(32)
    auth_url = (
        f"https://connect.linux.do/oauth2/authorize"
        f"?client_id={client_id}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri or 'http://localhost:5173/callback'}"
        f"&state={state}"
    )
    
    return LinuxDOAuthURL(auth_url=auth_url, state=state)


@router.post("/linuxdo/callback", response_model=LinuxDOUserInfo)
@limiter.limit("20/minute")  # 每分钟最多20次
async def linuxdo_callback(request: Request, data: LinuxDOCallback, db: Session = Depends(get_db)):
    """LinuxDO OAuth 回调"""
    client_id = get_config(db, "linuxdo_client_id")
    client_secret = get_config(db, "linuxdo_client_secret")
    redirect_uri = get_config(db, "linuxdo_redirect_uri")
    
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="LinuxDO OAuth 未配置")
    
    async with httpx.AsyncClient() as client:
        # 用 code 换取 token
        token_resp = await client.post(
            "https://connect.linux.do/oauth2/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": data.code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri or "http://localhost:5173/callback",
            }
        )
        
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="获取 token 失败")
        
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        
        # 获取用户信息
        user_resp = await client.get(
            "https://connect.linux.do/api/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="获取用户信息失败")
        
        user_data = user_resp.json()
    
    # 保存或更新用户
    linuxdo_id = str(user_data.get("id"))
    linuxdo_user = db.query(LinuxDOUser).filter(LinuxDOUser.linuxdo_id == linuxdo_id).first()
    
    if linuxdo_user:
        linuxdo_user.username = user_data.get("username", "")
        linuxdo_user.name = user_data.get("name")
        linuxdo_user.email = user_data.get("email")
        linuxdo_user.trust_level = user_data.get("trust_level", 0)
        linuxdo_user.avatar_url = user_data.get("avatar_url")
        linuxdo_user.last_login = datetime.utcnow()
    else:
        linuxdo_user = LinuxDOUser(
            linuxdo_id=linuxdo_id,
            username=user_data.get("username", ""),
            name=user_data.get("name"),
            email=user_data.get("email"),
            trust_level=user_data.get("trust_level", 0),
            avatar_url=user_data.get("avatar_url")
        )
        db.add(linuxdo_user)
    
    db.commit()
    db.refresh(linuxdo_user)
    
    # 生成 token
    simple_token = f"{linuxdo_user.id}:{secrets.token_urlsafe(32)}"
    
    return LinuxDOUserInfo(
        id=linuxdo_user.id,
        linuxdo_id=linuxdo_id,
        username=linuxdo_user.username,
        name=linuxdo_user.name,
        email=linuxdo_user.email,
        trust_level=linuxdo_user.trust_level,
        avatar_url=linuxdo_user.avatar_url,
        token=simple_token
    )


def get_linuxdo_user_from_token(db: Session, token: str) -> LinuxDOUser:
    """从 token 获取 LinuxDO 用户"""
    try:
        user_id = int(token.split(":")[0])
        user = db.query(LinuxDOUser).filter(LinuxDOUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        return user
    except:
        raise HTTPException(status_code=401, detail="无效的 token")


# ========== 用户状态 ==========
@router.get("/user/status")
async def get_user_status(token: str, db: Session = Depends(get_db)):
    """获取用户状态（是否已有邀请）"""
    user = get_linuxdo_user_from_token(db, token)
    
    # 查找该用户的邀请记录
    invite = db.query(InviteRecord).filter(
        InviteRecord.linuxdo_user_id == user.id
    ).order_by(InviteRecord.created_at.desc()).first()
    
    if invite:
        team = db.query(Team).filter(Team.id == invite.team_id).first()
        return UserStatusResponse(
            has_active_invite=True,
            team_name=team.name if team else None,
            invite_email=invite.email,
            invite_status=invite.status.value,
            invite_time=invite.created_at.isoformat()
        )
    
    return UserStatusResponse(has_active_invite=False)


# ========== 兑换码使用 ==========
class SeatStats(BaseModel):
    total_seats: int
    used_seats: int  # 已同步成员
    pending_seats: int  # 已邀请未接受
    available_seats: int  # 可用空位


@router.get("/seats", response_model=SeatStats)
async def get_seat_stats(db: Session = Depends(get_db)):
    """获取座位统计（公开，带缓存）
    
    使用本地缓存的成员数据，不实时调用 ChatGPT API
    """
    from app.cache import get_seat_stats_cache, set_seat_stats_cache
    
    # 尝试从缓存获取
    cached = get_seat_stats_cache()
    if cached:
        return SeatStats(**cached)
    
    # 从数据库获取
    teams = db.query(Team).filter(Team.is_active == True).all()
    
    total_seats = 0
    used_seats = 0
    
    for team in teams:
        total_seats += team.max_seats
        member_count = db.query(TeamMember).filter(TeamMember.team_id == team.id).count()
        used_seats += member_count
    
    available_seats = max(0, total_seats - used_seats)
    
    result = SeatStats(
        total_seats=total_seats,
        used_seats=used_seats,
        pending_seats=0,
        available_seats=available_seats
    )
    
    # 写入缓存（30秒）
    set_seat_stats_cache(result.model_dump())
    return result


@router.post("/redeem", response_model=RedeemResponse)
@limiter.limit("5/minute")  # 每分钟最多5次
async def use_redeem_code(request: Request, data: RedeemRequest, db: Session = Depends(get_db)):
    """使用兑换码加入 Team"""
    # 并发控制
    async with _redeem_semaphore:
        return await _do_redeem(data, db)


async def _do_redeem(data: RedeemRequest, db: Session):
    """实际执行兑换逻辑 - 排队模式"""
    from app.tasks import enqueue_invite
    from app.models import TeamGroup
    
    # 验证用户
    user = get_linuxdo_user_from_token(db, data.linuxdo_token)
    
    # 验证兑换码
    code = db.query(RedeemCode).filter(
        RedeemCode.code == data.redeem_code.strip().upper(),
        RedeemCode.is_active == True
    ).first()
    
    if not code:
        raise HTTPException(status_code=400, detail="兑换码无效")
    
    if code.expires_at and code.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="兑换码已过期")
    
    if code.used_count >= code.max_uses:
        raise HTTPException(status_code=400, detail="兑换码已用完")
    
    # 原子性增加使用次数
    from sqlalchemy import update
    result = db.execute(
        update(RedeemCode)
        .where(RedeemCode.id == code.id)
        .where(RedeemCode.used_count < RedeemCode.max_uses)
        .values(used_count=RedeemCode.used_count + 1)
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=400, detail="兑换码已用完")
    
    db.commit()
    
    # 确定分组 ID
    group_id = code.group_id
    if not group_id:
        # 默认使用 LinuxDO 分组
        group = db.query(TeamGroup).filter(TeamGroup.name == "LinuxDO").first()
        group_id = group.id if group else None
    
    # 加入队列
    try:
        await enqueue_invite(
            email=data.email.lower().strip(),
            redeem_code=code.code,
            group_id=group_id,
            linuxdo_user_id=user.id
        )
        
        return RedeemResponse(
            success=True,
            message="已加入队列，邀请将在几秒内发送，请稍后查收邮箱",
            team_name=None
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


# ========== 直接链接兑换（无需登录）==========
class DirectRedeemRequest(BaseModel):
    email: EmailStr
    code: str


class DirectRedeemResponse(BaseModel):
    success: bool
    message: str
    team_name: Optional[str] = None


@router.get("/queue-status")
async def get_queue_status_api():
    """获取邀请队列状态"""
    from app.tasks import get_queue_status
    return await get_queue_status()


@router.get("/direct/{code}")
async def get_direct_code_info(code: str, db: Session = Depends(get_db)):
    """获取直接兑换码信息（验证是否有效）"""
    redeem_code = db.query(RedeemCode).filter(
        RedeemCode.code == code.strip().upper(),
        RedeemCode.code_type == RedeemCodeType.DIRECT,
        RedeemCode.is_active == True
    ).first()
    
    if not redeem_code:
        raise HTTPException(status_code=404, detail="兑换码无效或不存在")
    
    if redeem_code.expires_at and redeem_code.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="兑换码已过期")
    
    if redeem_code.used_count >= redeem_code.max_uses:
        raise HTTPException(status_code=400, detail="兑换码已用完")
    
    return {
        "valid": True,
        "remaining": redeem_code.max_uses - redeem_code.used_count,
        "expires_at": redeem_code.expires_at.isoformat() if redeem_code.expires_at else None
    }


@router.post("/direct-redeem", response_model=DirectRedeemResponse)
@limiter.limit("5/minute")  # 每分钟最多5次
async def direct_redeem(request: Request, data: DirectRedeemRequest, db: Session = Depends(get_db)):
    """直接兑换（无需登录，只需邮箱和兑换码）"""
    # 并发控制
    async with _redeem_semaphore:
        return await _do_direct_redeem(data, db)


async def _do_direct_redeem(data: DirectRedeemRequest, db: Session):
    """实际执行直接兑换逻辑 - 排队模式"""
    from app.tasks import enqueue_invite
    
    # 验证兑换码
    code = db.query(RedeemCode).filter(
        RedeemCode.code == data.code.strip().upper(),
        RedeemCode.code_type == RedeemCodeType.DIRECT,
        RedeemCode.is_active == True
    ).first()
    
    if not code:
        raise HTTPException(status_code=400, detail="兑换码无效")
    
    if code.expires_at and code.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="兑换码已过期")
    
    if code.used_count >= code.max_uses:
        raise HTTPException(status_code=400, detail="兑换码已用完")
    
    # 原子性增加使用次数
    from sqlalchemy import update
    result = db.execute(
        update(RedeemCode)
        .where(RedeemCode.id == code.id)
        .where(RedeemCode.used_count < RedeemCode.max_uses)
        .values(used_count=RedeemCode.used_count + 1)
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=400, detail="兑换码已用完")
    
    db.commit()
    
    # 加入队列
    try:
        await enqueue_invite(
            email=data.email.lower().strip(),
            redeem_code=code.code,
            group_id=code.group_id
        )
        
        return DirectRedeemResponse(
            success=True,
            message="已加入队列，邀请将在几秒内发送，请稍后查收邮箱",
            team_name=None
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
