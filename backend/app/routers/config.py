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

router = APIRouter(prefix="/config", tags=["config"])


class ConfigItem(BaseModel):
    key: str
    value: Optional[str]
    description: Optional[str]


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
    email_enabled = get_config_value(db, "email_enabled", "false")
    if email_enabled.lower() != "true":
        return {"message": "邮件通知未启用", "alerts": []}
    
    alerts = []
    
    # 获取预警阈值
    member_threshold = int(get_config_value(db, "alert_member_threshold", "5"))
    token_days = int(get_config_value(db, "alert_token_days", "7"))
    
    # 检查所有活跃的 Team
    teams = db.query(Team).filter(Team.is_active == True).all()
    
    for team in teams:
        # 检查超员
        member_count = len(team.members)
        if member_count > member_threshold:
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
    
    # 发送预警邮件
    if alerts:
        send_alert_email(db, alerts)
    
    return {"message": f"检查完成，发现 {len(alerts)} 个预警", "alerts": alerts}
