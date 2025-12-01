# 系统配置管理 API
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import SystemConfig, User, Team
from app.services.auth import get_current_user
from app.services.email import send_email, send_alert_email
from app.services.telegram import send_telegram_message

router = APIRouter(prefix="/config", tags=["config"])


class ConfigItem(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None


class ConfigResponse(BaseModel):
    key: str
    value: Optional[str]
    description: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True


class ConfigListResponse(BaseModel):
    configs: List[ConfigResponse]


# 默认配置项
DEFAULT_CONFIGS = [
    {"key": "linuxdo_client_id", "description": "LinuxDO OAuth Client ID"},
    {"key": "linuxdo_client_secret", "description": "LinuxDO OAuth Client Secret"},
    {"key": "linuxdo_redirect_uri", "description": "LinuxDO OAuth 回调地址"},
    {"key": "site_url", "description": "站点 URL（用于生成链接）"},
    {"key": "site_title", "description": "站点标题"},
    {"key": "site_description", "description": "站点描述"},
    {"key": "min_trust_level", "description": "最低信任等级要求（0-4）"},
    # SMTP 邮件配置
    {"key": "smtp_host", "description": "SMTP 服务器地址"},
    {"key": "smtp_port", "description": "SMTP 端口（465 SSL / 587 TLS）"},
    {"key": "smtp_user", "description": "发件邮箱"},
    {"key": "smtp_password", "description": "邮箱授权码"},
    {"key": "admin_email", "description": "管理员邮箱（接收预警）"},
    {"key": "email_enabled", "description": "是否启用邮件通知"},
    {"key": "alert_member_threshold", "description": "超员预警阈值（默认5）"},
    {"key": "alert_token_days", "description": "Token过期预警天数（默认7）"},
    # Telegram 通知配置
    {"key": "telegram_bot_token", "description": "Telegram Bot Token"},
    {"key": "telegram_chat_id", "description": "Telegram Chat ID（群组或个人）"},
    {"key": "telegram_enabled", "description": "是否启用 Telegram 通知"},
    {"key": "telegram_notify_invite", "description": "新用户上车时通知"},
    {"key": "telegram_notify_alert", "description": "座位预警时通知"},
]


@router.get("", response_model=ConfigListResponse)
async def list_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有配置"""
    configs = db.query(SystemConfig).all()
    
    # 确保默认配置项存在
    existing_keys = {c.key for c in configs}
    for default in DEFAULT_CONFIGS:
        if default["key"] not in existing_keys:
            new_config = SystemConfig(
                key=default["key"],
                value="",
                description=default["description"]
            )
            db.add(new_config)
    db.commit()
    
    configs = db.query(SystemConfig).all()
    return ConfigListResponse(configs=[
        ConfigResponse(
            key=c.key,
            value=c.value if "secret" not in c.key.lower() else ("*" * 8 if c.value else ""),
            description=c.description,
            updated_at=c.updated_at
        ) for c in configs
    ])


@router.put("/{key}")
async def update_config(
    key: str,
    data: ConfigItem,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新配置"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    
    if config:
        # 如果是 secret 且值为 ****，不更新
        if "secret" in key.lower() and data.value and data.value.startswith("*"):
            pass
        else:
            config.value = data.value
        if data.description:
            config.description = data.description
    else:
        config = SystemConfig(
            key=key,
            value=data.value,
            description=data.description
        )
        db.add(config)
    
    db.commit()
    return {"message": "配置已更新", "key": key}


@router.post("/batch")
async def batch_update_configs(
    configs: List[ConfigItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新配置"""
    for item in configs:
        config = db.query(SystemConfig).filter(SystemConfig.key == item.key).first()
        
        if config:
            if "secret" in item.key.lower() and item.value and item.value.startswith("*"):
                continue
            config.value = item.value
            if item.description:
                config.description = item.description
        else:
            config = SystemConfig(
                key=item.key,
                value=item.value,
                description=item.description
            )
            db.add(config)
    
    db.commit()
    return {"message": f"已更新 {len(configs)} 项配置"}


@router.post("/test-email")
async def test_email(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送测试邮件"""
    success = send_email(
        db,
        "测试邮件",
        "<p>这是一封测试邮件，如果您收到此邮件，说明邮件配置正确。</p>"
    )
    if success:
        return {"message": "测试邮件已发送，请检查收件箱"}
    else:
        raise HTTPException(status_code=400, detail="邮件发送失败，请检查 SMTP 配置")


@router.post("/test-telegram")
async def test_telegram(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送测试 Telegram 消息"""
    from app.services.telegram import TelegramError
    
    bot_token = get_config_value(db, "telegram_bot_token")
    chat_id = get_config_value(db, "telegram_chat_id")
    
    if not bot_token or not chat_id:
        raise HTTPException(status_code=400, detail="请先配置 Telegram Bot Token 和 Chat ID")
    
    message = "🔔 <b>测试消息</b>\n\n这是一条测试消息，如果您收到此消息，说明 Telegram 配置正确。"
    
    try:
        await send_telegram_message(bot_token, chat_id, message)
        return {"message": "测试消息已发送，请检查 Telegram"}
    except TelegramError as e:
        raise HTTPException(status_code=400, detail=f"{e.message}: {e.detail}")


@router.post("/setup-telegram-webhook")
async def setup_telegram_webhook(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """设置 Telegram Bot Webhook 和命令菜单"""
    import httpx
    
    bot_token = get_config_value(db, "telegram_bot_token")
    site_url = get_config_value(db, "site_url")
    
    if not bot_token:
        raise HTTPException(status_code=400, detail="请先配置 Telegram Bot Token")
    
    if not site_url:
        raise HTTPException(status_code=400, detail="请先配置站点 URL（site_url）")
    
    webhook_url = f"{site_url.rstrip('/')}/api/v1/telegram/webhook"
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # 1. 设置 Webhook
            resp = await client.post(
                f"https://api.telegram.org/bot{bot_token}/setWebhook",
                json={"url": webhook_url}
            )
            result = resp.json()
            
            if not result.get("ok"):
                raise HTTPException(status_code=400, detail=f"Webhook 设置失败: {result.get('description')}")
            
            # 2. 设置命令菜单
            commands = [
                {"command": "start", "description": "显示帮助信息"},
                {"command": "status", "description": "查看系统状态"},
                {"command": "seats", "description": "座位统计"},
                {"command": "teams", "description": "Team 列表"},
                {"command": "alerts", "description": "查看预警"},
                {"command": "sync", "description": "同步所有成员"},
                {"command": "code", "description": "生成兑换码 (如: /code 5)"},
                {"command": "dcode", "description": "生成直接链接 (如: /dcode 5)"},
            ]
            
            await client.post(
                f"https://api.telegram.org/bot{bot_token}/setMyCommands",
                json={"commands": commands}
            )
            
            return {"message": f"设置成功！Webhook: {webhook_url}"}
    except httpx.TimeoutException:
        raise HTTPException(status_code=400, detail="连接超时")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def get_config_value(db: Session, key: str, default: str = "") -> str:
    """获取配置值"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return config.value if config and config.value else default


@router.post("/check-alerts")
async def check_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查并发送预警邮件"""
    from app.models import TeamMember, TeamGroup
    from app.services.email import send_group_seat_warning
    
    email_enabled = get_config_value(db, "email_enabled", "false")
    if email_enabled.lower() != "true":
        return {"message": "邮件通知未启用", "alerts": []}
    
    alerts = []
    
    # 获取预警阈值
    member_threshold = int(get_config_value(db, "alert_member_threshold", "5"))
    token_days = int(get_config_value(db, "alert_token_days", "7"))
    group_seat_threshold = int(get_config_value(db, "group_seat_warning_threshold", "5"))
    
    # 检查所有活跃的 Team
    teams = db.query(Team).filter(Team.is_active == True).all()
    
    for team in teams:
        # 检查超员（使用 TeamMember 表的真实数据）
        member_count = db.query(TeamMember).filter(TeamMember.team_id == team.id).count()
        max_seats = team.max_seats or 5
        
        if member_count >= max_seats:
            alerts.append({
                "type": "error",
                "team": team.name,
                "message": f"座位已满！当前 {member_count}/{max_seats} 人"
            })
        elif member_count > member_threshold:
            alerts.append({
                "type": "warning",
                "team": team.name,
                "message": f"成员数量 {member_count} 人，超过阈值 {member_threshold} 人"
            })
        
        # 检查 Token 过期
        if team.token_expires_at:
            days_left = (team.token_expires_at - datetime.utcnow()).days
            if days_left <= token_days:
                alert_type = "error" if days_left <= 3 else "warning"
                alerts.append({
                    "type": alert_type,
                    "team": team.name,
                    "message": f"Token 将在 {days_left} 天后过期" if days_left > 0 else "Token 已过期！"
                })
    
    # 检查分组空位（使用每个分组自己的阈值）
    groups = db.query(TeamGroup).all()
    for group in groups:
        # 获取分组的预警阈值，0 表示不预警
        group_threshold = group.alert_threshold if group.alert_threshold is not None else 5
        if group_threshold == 0:
            continue  # 该分组不需要预警
        
        group_teams = db.query(Team).filter(
            Team.group_id == group.id,
            Team.is_active == True
        ).all()
        
        if not group_teams:
            continue
        
        total_seats = sum(t.max_seats or 5 for t in group_teams)
        used_seats = 0
        for t in group_teams:
            used_seats += db.query(TeamMember).filter(TeamMember.team_id == t.id).count()
        
        available_seats = total_seats - used_seats
        
        if available_seats <= 0:
            alerts.append({
                "type": "error",
                "team": f"分组: {group.name}",
                "message": f"分组座位已满！（{used_seats}/{total_seats}）"
            })
            send_group_seat_warning(db, group.name, used_seats, total_seats, available_seats)
        elif available_seats <= group_threshold:
            alerts.append({
                "type": "warning",
                "team": f"分组: {group.name}",
                "message": f"分组仅剩 {available_seats} 个空位（{used_seats}/{total_seats}，阈值: {group_threshold}）"
            })
            send_group_seat_warning(db, group.name, used_seats, total_seats, available_seats)
    
    # 发送预警邮件
    if alerts:
        send_alert_email(db, alerts)
    
    # 发送 Telegram 预警
    await send_telegram_alerts(db, alerts)
    
    return {"message": f"检查完成，发现 {len(alerts)} 个预警", "alerts": alerts}


async def send_telegram_alerts(db: Session, alerts: list):
    """发送 Telegram 预警通知"""
    from app.services.telegram import send_telegram_message
    
    tg_enabled = get_config_value(db, "telegram_enabled")
    notify_alert = get_config_value(db, "telegram_notify_alert")
    
    if tg_enabled != "true" or notify_alert != "true":
        return
    
    bot_token = get_config_value(db, "telegram_bot_token")
    chat_id = get_config_value(db, "telegram_chat_id")
    
    if not bot_token or not chat_id:
        return
    
    if not alerts:
        return
    
    message = "⚠️ <b>系统预警</b>\n\n"
    for alert in alerts:
        icon = "🔴" if alert["type"] == "error" else "🟡"
        message += f"{icon} <b>{alert['team']}</b>\n   {alert['message']}\n\n"
    
    await send_telegram_message(bot_token, chat_id, message)
