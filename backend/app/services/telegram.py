# Telegram 通知服务
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    """发送 Telegram 消息"""
    if not bot_token or not chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            })
            
            if resp.status_code == 200:
                logger.info(f"Telegram message sent to {chat_id}")
                return True
            else:
                logger.warning(f"Telegram send failed: {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False


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
