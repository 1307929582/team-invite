# 通知设置路由
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import User
from app.services.auth import get_current_user
from app.services.email import (
    get_notification_settings,
    save_notification_settings,
    is_email_configured,
    test_email_connection,
    send_email,
    get_config,
    set_config
)
from app.schemas import MessageResponse

router = APIRouter(prefix="/notifications", tags=["通知设置"])


class NotificationSettings(BaseModel):
    enabled: bool = False
    token_expiring_days: int = 7
    seat_warning_threshold: int = 80
    notify_new_invite: bool = True
    notify_invite_accepted: bool = False
    daily_report_enabled: bool = False
    daily_report_hour: int = 9


class SmtpConfig(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    admin_email: str


@router.get("/settings")
async def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取通知设置"""
    settings = get_notification_settings(db)
    email_configured = is_email_configured(db)
    
    return {
        "settings": settings,
        "email_configured": email_configured
    }


@router.put("/settings")
async def update_settings(
    settings: NotificationSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新通知设置"""
    save_notification_settings(db, settings.model_dump())
    return {"message": "设置已保存", "success": True}


@router.get("/smtp")
async def get_smtp_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 SMTP 配置（密码脱敏）"""
    return {
        "smtp_host": get_config(db, "smtp_host") or "",
        "smtp_port": int(get_config(db, "smtp_port") or 587),
        "smtp_user": get_config(db, "smtp_user") or "",
        "smtp_password": "******" if get_config(db, "smtp_password") else "",
        "admin_email": get_config(db, "admin_email") or "",
        "configured": is_email_configured(db)
    }


@router.put("/smtp")
async def update_smtp_config(
    config: SmtpConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新 SMTP 配置"""
    set_config(db, "smtp_host", config.smtp_host, "SMTP 服务器地址")
    set_config(db, "smtp_port", str(config.smtp_port), "SMTP 端口")
    set_config(db, "smtp_user", config.smtp_user, "SMTP 用户名")
    if config.smtp_password != "******":
        set_config(db, "smtp_password", config.smtp_password, "SMTP 密码")
    set_config(db, "admin_email", config.admin_email, "管理员邮箱")
    
    return {"message": "SMTP 配置已保存", "success": True}


@router.post("/test")
async def test_smtp(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试 SMTP 连接"""
    result = test_email_connection(db)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/test-send")
async def test_send_email(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送测试邮件"""
    if not is_email_configured(db):
        raise HTTPException(status_code=400, detail="请先配置 SMTP")
    
    content = """
    <div style="padding: 20px; background: #ecfdf5; border-radius: 8px; border-left: 4px solid #10b981;">
        <h3 style="margin: 0 0 10px 0; color: #059669;">测试邮件</h3>
        <p style="margin: 0;">如果您收到这封邮件，说明邮件通知功能配置正确！</p>
    </div>
    """
    
    success = send_email(db, "测试邮件 - 配置成功", content)
    if not success:
        raise HTTPException(status_code=500, detail="邮件发送失败")
    
    return {"message": "测试邮件已发送", "success": True}
