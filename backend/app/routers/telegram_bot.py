# Telegram Bot 命令处理
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Team, TeamMember, User, RedeemCode, RedeemCodeType, SystemConfig, InviteRecord
from app.services.telegram import send_telegram_message
import logging

router = APIRouter(prefix="/telegram", tags=["telegram-bot"])
logger = logging.getLogger(__name__)


def get_config(db: Session, key: str) -> str:
    """获取系统配置"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return config.value if config and config.value else ""


def is_authorized(chat_id: str, db: Session) -> bool:
    """检查是否有权限操作"""
    allowed_chat_id = get_config(db, "telegram_chat_id")
    return str(chat_id) == str(allowed_chat_id)


async def handle_command(text: str, chat_id: str, db: Session, bot_token: str):
    """处理 Bot 命令"""
    text = text.strip()
    
    # /start - 欢迎信息
    if text == "/start" or text == "/help":
        msg = "🤖 <b>ChatGPT Team Manager Bot</b>\n\n"
        msg += "可用命令：\n"
        msg += "/status - 系统状态\n"
        msg += "/seats - 座位统计\n"
        msg += "/teams - Team 列表\n"
        msg += "/alerts - 查看预警\n"
        msg += "/sync - 同步所有成员\n"
        msg += "/code [数量] - 生成兑换码\n"
        msg += "/dcode [数量] - 生成直接链接码\n"
        await send_telegram_message(bot_token, chat_id, msg)
        return
    
    # /status - 系统状态
    if text == "/status":
        teams = db.query(Team).filter(Team.is_active == True).all()
        total_seats = sum(t.max_seats for t in teams)
        used_seats = 0
        for t in teams:
            used_seats += db.query(TeamMember).filter(TeamMember.team_id == t.id).count()
        
        active_codes = db.query(RedeemCode).filter(RedeemCode.is_active == True).count()
        
        msg = "📊 <b>系统状态</b>\n\n"
        msg += f"✅ 状态: 正常运行\n"
        msg += f"👥 Team 数量: {len(teams)}\n"
        msg += f"💺 座位: {used_seats}/{total_seats}\n"
        msg += f"🎫 有效兑换码: {active_codes}\n"
        await send_telegram_message(bot_token, chat_id, msg)
        return
    
    # /seats - 座位统计
    if text == "/seats":
        teams = db.query(Team).filter(Team.is_active == True).all()
        
        msg = "💺 <b>座位统计</b>\n\n"
        total_used = 0
        total_max = 0
        
        for team in teams:
            member_count = db.query(TeamMember).filter(TeamMember.team_id == team.id).count()
            total_used += member_count
            total_max += team.max_seats
            
            # 使用进度条
            percent = int((member_count / team.max_seats) * 100) if team.max_seats > 0 else 0
            bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
            
            status = "🔴" if member_count >= team.max_seats else "🟢"
            msg += f"{status} <b>{team.name}</b>\n"
            msg += f"   {bar} {member_count}/{team.max_seats}\n\n"
        
        msg += f"📈 总计: {total_used}/{total_max}"
        await send_telegram_message(bot_token, chat_id, msg)
        return

    # /teams - Team 列表
    if text == "/teams":
        teams = db.query(Team).filter(Team.is_active == True).all()
        
        msg = "👥 <b>Team 列表</b>\n\n"
        for team in teams:
            member_count = db.query(TeamMember).filter(TeamMember.team_id == team.id).count()
            status = "🔴" if member_count >= team.max_seats else "🟢"
            msg += f"{status} {team.name} ({member_count}/{team.max_seats})\n"
        
        await send_telegram_message(bot_token, chat_id, msg)
        return
    
    # /alerts - 查看预警
    if text == "/alerts":
        teams = db.query(Team).filter(Team.is_active == True).all()
        alerts = []
        
        for team in teams:
            member_count = db.query(TeamMember).filter(TeamMember.team_id == team.id).count()
            
            # 座位满
            if member_count >= team.max_seats:
                alerts.append(f"🔴 {team.name}: 座位已满 ({member_count}/{team.max_seats})")
            elif member_count >= team.max_seats - 2:
                alerts.append(f"🟡 {team.name}: 座位即将满 ({member_count}/{team.max_seats})")
            
            # 未授权成员
            unauthorized = db.query(TeamMember).filter(
                TeamMember.team_id == team.id,
                TeamMember.is_unauthorized == True
            ).count()
            if unauthorized > 0:
                alerts.append(f"🚨 {team.name}: {unauthorized} 个未授权成员")
        
        if alerts:
            msg = "⚠️ <b>系统预警</b>\n\n" + "\n".join(alerts)
        else:
            msg = "✅ <b>无预警</b>\n\n系统运行正常，没有需要关注的问题。"
        
        await send_telegram_message(bot_token, chat_id, msg)
        return
    
    # /sync - 同步所有成员
    if text == "/sync":
        await send_telegram_message(bot_token, chat_id, "🔄 开始同步所有 Team 成员...")
        
        from app.services.chatgpt_api import ChatGPTAPI
        from datetime import datetime
        
        teams = db.query(Team).filter(Team.is_active == True).all()
        success = 0
        fail = 0
        
        for team in teams:
            try:
                api = ChatGPTAPI(team.session_token, team.device_id or "")
                result = await api.get_members(team.account_id)
                members_data = result.get("items", result.get("users", []))
                
                # 清除旧数据
                db.query(TeamMember).filter(TeamMember.team_id == team.id).delete()
                
                # 插入新数据
                for m in members_data:
                    email = m.get("email", "").lower().strip()
                    if email:
                        member = TeamMember(
                            team_id=team.id,
                            email=email,
                            name=m.get("name", ""),
                            role=m.get("role", "member"),
                            chatgpt_user_id=m.get("id", ""),
                            synced_at=datetime.utcnow()
                        )
                        db.add(member)
                
                db.commit()
                success += 1
            except Exception as e:
                logger.error(f"Sync {team.name} failed: {e}")
                fail += 1
        
        msg = f"✅ <b>同步完成</b>\n\n成功: {success}\n失败: {fail}"
        await send_telegram_message(bot_token, chat_id, msg)
        return
    
    # /code [数量] - 生成 LinuxDO 兑换码
    if text.startswith("/code"):
        parts = text.split()
        count = int(parts[1]) if len(parts) > 1 else 1
        count = min(count, 20)  # 最多 20 个
        
        import secrets
        import string
        
        codes = []
        for _ in range(count):
            code_str = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            code = RedeemCode(
                code=code_str,
                code_type=RedeemCodeType.LINUXDO,
                max_uses=1,
                is_active=True
            )
            db.add(code)
            codes.append(code_str)
        
        db.commit()
        
        msg = f"🎫 <b>生成 {count} 个兑换码</b>\n\n"
        msg += "\n".join([f"<code>{c}</code>" for c in codes])
        await send_telegram_message(bot_token, chat_id, msg)
        return
    
    # /dcode [数量] - 生成直接链接码
    if text.startswith("/dcode"):
        parts = text.split()
        count = int(parts[1]) if len(parts) > 1 else 1
        count = min(count, 20)
        
        import secrets
        import string
        
        codes = []
        for _ in range(count):
            code_str = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            code = RedeemCode(
                code=code_str,
                code_type=RedeemCodeType.DIRECT,
                max_uses=1,
                is_active=True
            )
            db.add(code)
            codes.append(code_str)
        
        db.commit()
        
        # 获取站点域名
        site_url = get_config(db, "site_url") or "https://your-domain.com"
        
        msg = f"🔗 <b>生成 {count} 个直接链接</b>\n\n"
        for c in codes:
            msg += f"{site_url}/invite/{c}\n"
        await send_telegram_message(bot_token, chat_id, msg)
        return
    
    # 未知命令
    msg = "❓ 未知命令，发送 /help 查看可用命令"
    await send_telegram_message(bot_token, chat_id, msg)


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Telegram Webhook 接收消息"""
    try:
        data = await request.json()
        logger.info(f"Telegram webhook: {data}")
        
        # 获取消息
        message = data.get("message", {})
        text = message.get("text", "")
        chat_id = str(message.get("chat", {}).get("id", ""))
        
        if not text or not chat_id:
            return {"ok": True}
        
        # 获取数据库连接
        db = SessionLocal()
        try:
            # 检查权限
            if not is_authorized(chat_id, db):
                bot_token = get_config(db, "telegram_bot_token")
                if bot_token:
                    await send_telegram_message(bot_token, chat_id, "⛔ 无权限操作")
                return {"ok": True}
            
            # 处理命令
            bot_token = get_config(db, "telegram_bot_token")
            if bot_token and text.startswith("/"):
                await handle_command(text, chat_id, db, bot_token)
        finally:
            db.close()
        
        return {"ok": True}
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return {"ok": True}
