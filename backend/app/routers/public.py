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
    """获取有空位的 Team
    
    Args:
        group_id: 指定分组 ID
        group_name: 指定分组名称（如果 group_id 为空，则按名称查找）
    
    座位判断逻辑：
    - 只依赖 TeamMember 表的成员数（定时同步的真实数据）
    - 不再统计本地的 pending 邀请记录，因为可能不准确
    - 这样当有人退出后，同步更新后空位就能被使用
    """
    team_query = db.query(Team).filter(Team.is_active == True)
    
    if group_id:
        team_query = team_query.filter(Team.group_id == group_id)
    elif group_name:
        # 按分组名称查找
        from app.models import TeamGroup
        group = db.query(TeamGroup).filter(TeamGroup.name == group_name).first()
        if group:
            team_query = team_query.filter(Team.group_id == group.id)
        else:
            # 分组不存在，返回 None
            return None
    
    teams = team_query.with_for_update().all()
    
    for team in teams:
        # 只检查已同步的成员数（来自定时同步，是真实数据）
        member_count = db.query(TeamMember).filter(TeamMember.team_id == team.id).count()
        
        # 有空位就返回这个 Team
        if member_count < team.max_seats:
            return team
    
    return None


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
@limiter.limit("10/minute")  # 每分钟最多10次
async def use_redeem_code(request: Request, data: RedeemRequest, db: Session = Depends(get_db)):
    """使用兑换码加入 Team"""
    # 验证用户
    user = get_linuxdo_user_from_token(db, data.linuxdo_token)
    
    # 防止暴力破解：检查该用户最近的失败尝试次数
    from datetime import timedelta
    recent_time = datetime.utcnow() - timedelta(minutes=5)
    recent_failed = db.query(InviteRecord).filter(
        InviteRecord.linuxdo_user_id == user.id,
        InviteRecord.status == InviteStatus.FAILED,
        InviteRecord.created_at >= recent_time
    ).count()
    
    if recent_failed >= 5:
        raise HTTPException(
            status_code=429, 
            detail="尝试次数过多，请5分钟后再试"
        )
    
    # 验证兑换码（加锁防止并发）
    code = db.query(RedeemCode).filter(
        RedeemCode.code == data.redeem_code.strip().upper(),
        RedeemCode.is_active == True
    ).with_for_update().first()
    
    if not code:
        raise HTTPException(status_code=400, detail="兑换码无效")
    
    if code.expires_at and code.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="兑换码已过期")
    
    if code.used_count >= code.max_uses:
        raise HTTPException(status_code=400, detail="兑换码已用完")
    
    # 原子性增加使用次数，防止并发超额
    from sqlalchemy import update
    result = db.execute(
        update(RedeemCode)
        .where(RedeemCode.id == code.id)
        .where(RedeemCode.used_count < RedeemCode.max_uses)
        .values(used_count=RedeemCode.used_count + 1)
    )
    
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="兑换码已用完")
    
    # 查找有空位的 Team
    # LinuxDO 类型兑换码：优先使用 code.group_id，否则强制使用 "LinuxDO" 分组
    if code.group_id:
        available_team = get_available_team(db, group_id=code.group_id)
    else:
        # 没有指定分组时，LinuxDO 兑换码强制使用 LinuxDO 分组
        available_team = get_available_team(db, group_name="LinuxDO")
    
    if not available_team:
        raise HTTPException(status_code=400, detail="所有 Team 已满，请稍后再试")
    
    # 发送邀请
    try:
        api = ChatGPTAPI(available_team.session_token, available_team.device_id or "")
        result = await api.invite_members(
            available_team.account_id, 
            [data.email.lower().strip()]
        )
        
        # 记录邀请（使用次数已在前面原子更新）
        invite = InviteRecord(
            team_id=available_team.id,
            email=data.email.lower().strip(),
            linuxdo_user_id=user.id,
            status=InviteStatus.SUCCESS,
            redeem_code=code.code,
            batch_id=f"redeem-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        )
        db.add(invite)
        
        # 记录操作日志
        log = OperationLog(
            action="自助邀请",
            target=data.email.lower().strip(),
            team_id=available_team.id,
            details=f"LinuxDO用户 {user.username} 使用兑换码 {code.code} 邀请 {data.email}"
        )
        db.add(log)
        db.commit()
        
        # 发送 Telegram 通知
        await send_invite_telegram_notify(db, data.email, available_team.name, code.code, user.username)
        
        return RedeemResponse(
            success=True,
            message="邀请已发送！请查收邮箱并接受邀请",
            team_name=available_team.name
        )
    except ChatGPTAPIError as e:
        raise HTTPException(status_code=400, detail=f"邀请失败: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"邀请失败: {str(e)}")


# ========== 直接链接兑换（无需登录）==========
class DirectRedeemRequest(BaseModel):
    email: EmailStr
    code: str


class DirectRedeemResponse(BaseModel):
    success: bool
    message: str
    team_name: Optional[str] = None


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
@limiter.limit("10/minute")  # 每分钟最多10次
async def direct_redeem(request: Request, data: DirectRedeemRequest, db: Session = Depends(get_db)):
    """直接兑换（无需登录，只需邮箱和兑换码）"""
    # 验证兑换码（加锁防止并发）
    code = db.query(RedeemCode).filter(
        RedeemCode.code == data.code.strip().upper(),
        RedeemCode.code_type == RedeemCodeType.DIRECT,
        RedeemCode.is_active == True
    ).with_for_update().first()
    
    if not code:
        raise HTTPException(status_code=400, detail="兑换码无效")
    
    if code.expires_at and code.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="兑换码已过期")
    
    if code.used_count >= code.max_uses:
        raise HTTPException(status_code=400, detail="兑换码已用完")
    
    # 原子性增加使用次数，防止并发超额
    from sqlalchemy import update
    result = db.execute(
        update(RedeemCode)
        .where(RedeemCode.id == code.id)
        .where(RedeemCode.used_count < RedeemCode.max_uses)
        .values(used_count=RedeemCode.used_count + 1)
    )
    
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="兑换码已用完")
    
    # 查找有空位的 Team
    available_team = get_available_team(db, code.group_id)
    
    if not available_team:
            raise HTTPException(status_code=400, detail="所有 Team 已满，请稍后再试")
    
    # 发送邀请
    try:
        api = ChatGPTAPI(available_team.session_token, available_team.device_id or "")
        await api.invite_members(
            available_team.account_id, 
            [data.email.lower().strip()]
        )
        
        # 记录邀请（使用次数已在前面原子更新）
        invite = InviteRecord(
            team_id=available_team.id,
            email=data.email.lower().strip(),
            status=InviteStatus.SUCCESS,
            redeem_code=code.code,
            batch_id=f"direct-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        )
        db.add(invite)
        
        # 记录操作日志
        log = OperationLog(
            action="直接邀请",
            target=data.email.lower().strip(),
            team_id=available_team.id,
            details=f"使用直接链接 {code.code} 邀请 {data.email}"
        )
        db.add(log)
        db.commit()
        
        # 发送 Telegram 通知
        await send_invite_telegram_notify(db, data.email, available_team.name, code.code)
        
        return DirectRedeemResponse(
            success=True,
            message="邀请已发送！请查收邮箱并接受邀请",
            team_name=available_team.name
        )
    except ChatGPTAPIError as e:
        raise HTTPException(status_code=400, detail=f"邀请失败: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"邀请失败: {str(e)}")
