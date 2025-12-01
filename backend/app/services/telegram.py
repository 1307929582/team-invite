# Telegram 通知服务
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TelegramError(Exception):
    """Telegram 发送错误"""
    def __init__(self, message: str, detail: str = ""):
        self.message = message
        self.detail = detail
        super().__init__(message)


async def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    """发送 Telegram 消息"""
    if not bot_token or not chat_id:
        raise TelegramError("未配置", "请先配置 Bot Token 和 Chat ID")
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            })
            
            if resp.status_code == 200:
                logger.info(f"Telegram message sent to {chat_id}")
                return True
            else:
                # 解析 Telegram API 错误
                try:
                    error_data = resp.json()
                    error_desc = error_data.get("description", resp.text)
                except:
                    error_desc = resp.text
                logger.warning(f"Telegram send failed: {error_desc}")
                raise TelegramError("发送失败", error_desc)
    except TelegramError:
        raise
    except httpx.TimeoutException:
        logger.error("Telegram timeout")
        raise TelegramError("连接超时", "无法连接到 Telegram 服务器，请检查网络或代理设置")
    except httpx.ConnectError as e:
        logger.error(f"Telegram connect error: {e}")
        raise TelegramError("连接失败", "无法连接到 Telegram 服务器，服务器可能需要配置代理")
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        raise TelegramError("发送失败", str(e))


async def notify_new_invite(
    bot_token: str, 
    chat_id: str, 
    email: str, 
    team_name: str, 
    redeem_code: Optional[str] = None,
    username: Optional[str] = None
):
    """通知新用户上车"""
    message = f"🎉 <b>新用户上车</b>\n\n"
    message += f"📧 邮箱: <code>{email}</code>\n"
    message += f"👥 Team: {team_name}\n"
    if redeem_code:
        message += f"🎫 兑换码: <code>{redeem_code}</code>\n"
    if username:
        message += f"👤 LinuxDO: {username}\n"
    
    await send_telegram_message(bot_token, chat_id, message)


async def notify_seat_alert(
    bot_token: str,
    chat_id: str,
    team_name: str,
    used_seats: int,
    total_seats: int,
    threshold: int
):
    """座位预警通知"""
    available = total_seats - used_seats
    percentage = int((used_seats / total_seats) * 100)
    
    message = f"⚠️ <b>座位预警</b>\n\n"
    message += f"👥 Team: {team_name}\n"
    message += f"📊 使用率: {percentage}%\n"
    message += f"💺 已用/总数: {used_seats}/{total_seats}\n"
    message += f"🔔 剩余座位: {available}\n"
    message += f"\n预警阈值: 剩余 {threshold} 个座位"
    
    await send_telegram_message(bot_token, chat_id, message)


async def notify_token_expiry(
    bot_token: str,
    chat_id: str,
    team_name: str,
    days_left: int
):
    """Token 过期提醒"""
    if days_left <= 0:
        message = f"🔴 <b>Token 已过期</b>\n\n"
        message += f"👥 Team: {team_name}\n"
        message += f"⚠️ Token 已过期，请立即更新！"
    elif days_left <= 3:
        message = f"🟠 <b>Token 即将过期</b>\n\n"
        message += f"👥 Team: {team_name}\n"
        message += f"⏰ 剩余时间: {days_left} 天\n"
        message += f"⚠️ 请尽快更新 Token！"
    else:
        message = f"🟡 <b>Token 过期提醒</b>\n\n"
        message += f"👥 Team: {team_name}\n"
        message += f"⏰ 剩余时间: {days_left} 天"
    
    await send_telegram_message(bot_token, chat_id, message)


async def notify_daily_stats(
    bot_token: str,
    chat_id: str,
    total_teams: int,
    total_seats: int,
    used_seats: int,
    today_invites: int
):
    """每日统计通知"""
    available = total_seats - used_seats
    usage_rate = int((used_seats / total_seats) * 100) if total_seats > 0 else 0
    
    message = f"📊 <b>每日统计</b>\n\n"
    message += f"👥 Team 数量: {total_teams}\n"
    message += f"💺 总座位: {total_seats}\n"
    message += f"✅ 已使用: {used_seats} ({usage_rate}%)\n"
    message += f"🔓 可用: {available}\n"
    message += f"📨 今日邀请: {today_invites}"
    
    await send_telegram_message(bot_token, chat_id, message)


# ========== 管理操作通知 ==========

async def notify_team_created(bot_token: str, chat_id: str, team_name: str, max_seats: int, operator: str):
    """通知新建 Team"""
    message = f"➕ <b>新建 Team</b>\n\n"
    message += f"👥 名称: {team_name}\n"
    message += f"💺 座位数: {max_seats}\n"
    message += f"👤 操作人: {operator}"
    
    try:
        await send_telegram_message(bot_token, chat_id, message)
    except:
        pass


async def notify_team_deleted(bot_token: str, chat_id: str, team_name: str, operator: str):
    """通知删除 Team"""
    message = f"🗑️ <b>删除 Team</b>\n\n"
    message += f"👥 名称: {team_name}\n"
    message += f"👤 操作人: {operator}"
    
    try:
        await send_telegram_message(bot_token, chat_id, message)
    except:
        pass


async def notify_member_removed(bot_token: str, chat_id: str, email: str, team_name: str, operator: str):
    """通知移除成员"""
    message = f"👋 <b>移除成员</b>\n\n"
    message += f"📧 邮箱: <code>{email}</code>\n"
    message += f"👥 Team: {team_name}\n"
    message += f"👤 操作人: {operator}"
    
    try:
        await send_telegram_message(bot_token, chat_id, message)
    except:
        pass


async def notify_invite_cancelled(bot_token: str, chat_id: str, email: str, team_name: str, operator: str):
    """通知取消邀请"""
    message = f"❌ <b>取消邀请</b>\n\n"
    message += f"📧 邮箱: <code>{email}</code>\n"
    message += f"👥 Team: {team_name}\n"
    message += f"👤 操作人: {operator}"
    
    try:
        await send_telegram_message(bot_token, chat_id, message)
    except:
        pass


async def notify_redeem_codes_created(bot_token: str, chat_id: str, count: int, code_type: str, max_uses: int, operator: str):
    """通知创建兑换码"""
    type_name = "直接链接" if code_type == "direct" else "LinuxDO"
    message = f"🎫 <b>创建兑换码</b>\n\n"
    message += f"📦 数量: {count} 个\n"
    message += f"🏷️ 类型: {type_name}\n"
    message += f"🔢 每码可用: {max_uses} 次\n"
    message += f"👤 操作人: {operator}"
    
    try:
        await send_telegram_message(bot_token, chat_id, message)
    except:
        pass


async def notify_admin_created(bot_token: str, chat_id: str, username: str, role: str, operator: str):
    """通知创建管理员"""
    role_name = "管理员" if role == "admin" else "操作员"
    message = f"👤 <b>新建管理员</b>\n\n"
    message += f"📛 用户名: {username}\n"
    message += f"🔑 角色: {role_name}\n"
    message += f"👤 操作人: {operator}"
    
    try:
        await send_telegram_message(bot_token, chat_id, message)
    except:
        pass


async def notify_batch_invite(bot_token: str, chat_id: str, team_name: str, total: int, success: int, fail: int, operator: str):
    """通知批量邀请"""
    message = f"📨 <b>批量邀请</b>\n\n"
    message += f"👥 Team: {team_name}\n"
    message += f"📊 总数: {total}\n"
    message += f"✅ 成功: {success}\n"
    message += f"❌ 失败: {fail}\n"
    message += f"👤 操作人: {operator}"
    
    try:
        await send_telegram_message(bot_token, chat_id, message)
    except:
        pass


# ========== 统一通知入口 ==========

async def send_admin_notification(db, action: str, **kwargs):
    """统一的管理操作通知入口
    
    自动从数据库获取 Telegram 配置并发送通知
    """
    from app.models import SystemConfig
    
    def get_config(key: str) -> str:
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        return config.value if config and config.value else ""
    
    # 检查是否启用
    if get_config("telegram_enabled") != "true":
        return
    
    bot_token = get_config("telegram_bot_token")
    chat_id = get_config("telegram_chat_id")
    
    if not bot_token or not chat_id:
        return
    
    try:
        if action == "team_created":
            await notify_team_created(bot_token, chat_id, kwargs.get("team_name", ""), kwargs.get("max_seats", 0), kwargs.get("operator", ""))
        elif action == "team_deleted":
            await notify_team_deleted(bot_token, chat_id, kwargs.get("team_name", ""), kwargs.get("operator", ""))
        elif action == "member_removed":
            await notify_member_removed(bot_token, chat_id, kwargs.get("email", ""), kwargs.get("team_name", ""), kwargs.get("operator", ""))
        elif action == "invite_cancelled":
            await notify_invite_cancelled(bot_token, chat_id, kwargs.get("email", ""), kwargs.get("team_name", ""), kwargs.get("operator", ""))
        elif action == "redeem_codes_created":
            await notify_redeem_codes_created(bot_token, chat_id, kwargs.get("count", 0), kwargs.get("code_type", ""), kwargs.get("max_uses", 0), kwargs.get("operator", ""))
        elif action == "admin_created":
            await notify_admin_created(bot_token, chat_id, kwargs.get("username", ""), kwargs.get("role", ""), kwargs.get("operator", ""))
        elif action == "batch_invite":
            await notify_batch_invite(bot_token, chat_id, kwargs.get("team_name", ""), kwargs.get("total", 0), kwargs.get("success", 0), kwargs.get("fail", 0), kwargs.get("operator", ""))
        elif action == "unauthorized_members":
            await notify_unauthorized_members(bot_token, chat_id, kwargs.get("team_name", ""), kwargs.get("members", []))
    except Exception as e:
        logger.warning(f"Admin notification failed: {e}")


async def notify_unauthorized_members(bot_token: str, chat_id: str, team_name: str, members: list):
    """通知发现未授权成员"""
    if not members:
        return
    
    message = f"🚨 <b>发现未授权成员</b>\n\n"
    message += f"👥 Team: {team_name}\n"
    message += f"⚠️ 以下成员不是通过系统邀请的：\n\n"
    
    for email in members[:10]:  # 最多显示10个
        message += f"• <code>{email}</code>\n"
    
    if len(members) > 10:
        message += f"\n... 还有 {len(members) - 10} 个\n"
    
    message += f"\n💡 请检查是否有人私自拉人进 Team"
    
    try:
        await send_telegram_message(bot_token, chat_id, message)
    except:
        pass
