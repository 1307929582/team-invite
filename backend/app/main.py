# FastAPI 主入口
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import init_db, SessionLocal
from app.routers import auth, teams, invites, dashboard, public, redeem, config, users, setup, groups, invite_records, admins
from app.logger import setup_logging, get_logger
from app.limiter import limiter, rate_limit_exceeded_handler

# 初始化日志
setup_logging(level="INFO" if not settings.DEBUG else "DEBUG")
logger = get_logger(__name__)


async def sync_all_teams():
    """定时同步所有 Team 成员"""
    from app.models import Team, TeamMember, InviteRecord, InviteStatus
    from app.services.chatgpt_api import ChatGPTAPI, ChatGPTAPIError
    from datetime import datetime
    
    db = SessionLocal()
    try:
        teams_list = db.query(Team).filter(Team.is_active == True).all()
        
        for team in teams_list:
            try:
                api = ChatGPTAPI(team.session_token, team.device_id or "", team.cookie or "")
                result = await api.get_members(team.account_id)
                members_data = result.get("items", result.get("users", []))
                
                # 获取成员邮箱列表
                member_emails = set()
                for m in members_data:
                    email = m.get("email", "").lower().strip()
                    if email:
                        member_emails.add(email)
                
                # 更新邀请记录：如果邮箱已在成员列表中，标记为已接受
                pending_invites = db.query(InviteRecord).filter(
                    InviteRecord.team_id == team.id,
                    InviteRecord.status == InviteStatus.SUCCESS,
                    InviteRecord.accepted_at == None
                ).all()
                
                for invite in pending_invites:
                    if invite.email.lower().strip() in member_emails:
                        invite.accepted_at = datetime.utcnow()
                
                # 清除旧成员数据
                db.query(TeamMember).filter(TeamMember.team_id == team.id).delete()
                
                # 插入新成员数据（去重）
                seen_emails = set()
                for m in members_data:
                    email = m.get("email", "").lower().strip()
                    if not email or email in seen_emails:
                        continue
                    seen_emails.add(email)
                    
                    member = TeamMember(
                        team_id=team.id,
                        email=email,
                        name=m.get("name", m.get("display_name", "")),
                        role=m.get("role", "member"),
                        chatgpt_user_id=m.get("id", m.get("user_id", "")),
                        synced_at=datetime.utcnow()
                    )
                    db.add(member)
                
                db.commit()
                logger.info("Team sync completed", extra={
                    "team": team.name,
                    "member_count": len(members_data)
                })
                
            except ChatGPTAPIError as e:
                logger.error("Team sync failed", extra={
                    "team": team.name,
                    "error": e.message
                })
            except Exception as e:
                logger.exception("Team sync exception", extra={
                    "team": team.name,
                    "error": str(e)
                })
            
            # 每个 Team 间隔 2 秒，避免请求过快
            await asyncio.sleep(2)
            
    finally:
        db.close()


async def check_and_send_alerts():
    """检查预警并发送邮件"""
    from app.models import Team, TeamMember
    from app.services.email import send_alert_email
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        alerts = []
        teams_list = db.query(Team).filter(Team.is_active == True).all()
        
        for team in teams_list:
            # 检查成员数量
            member_count = db.query(TeamMember).filter(TeamMember.team_id == team.id).count()
            
            if member_count > 5:
                alerts.append({
                    "type": "error",
                    "team": team.name,
                    "message": f"成员超限！当前 {member_count} 人，超过 5 人限制，有封号风险！"
                })
            
            # 检查 Token 过期
            if team.token_expires_at:
                days_left = (team.token_expires_at - datetime.utcnow()).days
                if days_left <= 0:
                    alerts.append({
                        "type": "error",
                        "team": team.name,
                        "message": "Token 已过期，请尽快更新"
                    })
                elif days_left <= 7:
                    alerts.append({
                        "type": "warning",
                        "team": team.name,
                        "message": f"Token 将在 {days_left} 天后过期"
                    })
        
        if alerts:
            send_alert_email(db, alerts)
            logger.info(f"Sent {len(alerts)} alerts via email")
            
    except Exception as e:
        logger.exception("Alert check error", extra={"error": str(e)})
    finally:
        db.close()


async def periodic_sync():
    """定时任务：每 5 分钟同步一次 Team 成员"""
    alert_counter = 0  # 每小时检查一次预警
    while True:
        await asyncio.sleep(300)  # 5 分钟
        try:
            logger.info("Starting periodic sync")
            await sync_all_teams()
            
            # 每小时检查一次预警（12 * 5分钟 = 60分钟）
            alert_counter += 1
            if alert_counter >= 12:
                await check_and_send_alerts()
                alert_counter = 0
            
            logger.info("Periodic sync completed")
        except Exception as e:
            logger.exception("Periodic sync error", extra={"error": str(e)})


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    import os
    logger.info("Application starting", extra={
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "pid": os.getpid()
    })
    # 启动时初始化数据库
    init_db()
    
    # 只在主 worker 中启动定时任务（通过文件锁实现）
    sync_task = None
    lock_file = "/tmp/team_sync.lock"
    lock_acquired = False
    
    try:
        # 尝试获取锁（非阻塞）
        import fcntl
        lock_fd = open(lock_file, 'w')
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_acquired = True
        lock_fd.write(str(os.getpid()))
        lock_fd.flush()
        logger.info("Acquired sync lock, starting periodic sync task", extra={"pid": os.getpid()})
        sync_task = asyncio.create_task(periodic_sync())
    except (IOError, OSError):
        logger.info("Another worker has sync lock, skipping periodic sync", extra={"pid": os.getpid()})
    
    yield
    
    # 关闭时取消任务
    logger.info("Application shutting down")
    if sync_task:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass
    if lock_acquired:
        lock_fd.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ChatGPT Team 集中管理平台 API",
    lifespan=lifespan
)

# 添加限流器
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    import time
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # 只记录 API 请求，跳过静态资源
    if request.url.path.startswith("/api"):
        logger.info("API request", extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(process_time * 1000, 2),
            "client_ip": request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        })
    
    return response

# 公开 API（无需认证）
app.include_router(setup.router, prefix=settings.API_PREFIX)
app.include_router(public.router, prefix=settings.API_PREFIX)

# 管理员 API（需要认证）
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(teams.router, prefix=settings.API_PREFIX)
app.include_router(invites.router, prefix=settings.API_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_PREFIX)
app.include_router(redeem.router, prefix=settings.API_PREFIX)
app.include_router(config.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(groups.router, prefix=settings.API_PREFIX)
app.include_router(invite_records.router, prefix=settings.API_PREFIX)
app.include_router(admins.router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
