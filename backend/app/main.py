# FastAPI 主入口
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, SessionLocal
from app.routers import auth, teams, invites, dashboard, public, redeem, config, users, setup


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
                
                # 插入新成员数据
                for m in members_data:
                    member = TeamMember(
                        team_id=team.id,
                        email=m.get("email", ""),
                        name=m.get("name", m.get("display_name", "")),
                        role=m.get("role", "member"),
                        chatgpt_user_id=m.get("id", m.get("user_id", "")),
                        synced_at=datetime.utcnow()
                    )
                    db.add(member)
                
                db.commit()
                print(f"[Sync] Team {team.name} 同步完成，成员数: {len(members_data)}")
                
            except ChatGPTAPIError as e:
                print(f"[Sync] Team {team.name} 同步失败: {e.message}")
            except Exception as e:
                print(f"[Sync] Team {team.name} 同步异常: {str(e)}")
            
            # 每个 Team 间隔 2 秒，避免请求过快
            await asyncio.sleep(2)
            
    finally:
        db.close()


async def periodic_sync():
    """定时任务：每 5 分钟同步一次"""
    while True:
        await asyncio.sleep(300)  # 5 分钟
        try:
            print("[Sync] 开始定时同步...")
            await sync_all_teams()
            print("[Sync] 定时同步完成")
        except Exception as e:
            print(f"[Sync] 定时同步出错: {str(e)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时初始化数据库
    init_db()
    # 启动定时同步任务
    sync_task = asyncio.create_task(periodic_sync())
    yield
    # 关闭时取消任务
    sync_task.cancel()
    try:
        await sync_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ChatGPT Team 集中管理平台 API",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
