# 邮件通知服务
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import SystemConfig
from app.logger import get_logger

logger = get_logger(__name__)


# 通知类型
class NotificationType:
    TOKEN_EXPIRING = "token_expiring"      # Token 即将过期
    TOKEN_EXPIRED = "token_expired"        # Token 已过期
    SEAT_WARNING = "seat_warning"          # 座位容量预警
    SEAT_FULL = "seat_full"                # 座位已满
    NEW_INVITE = "new_invite"              # 新邀请发送
    INVITE_ACCEPTED = "invite_accepted"    # 邀请已接受
    DAILY_REPORT = "daily_report"          # 每日报告


def get_config(db: Session, key: str) -> Optional[str]:
    """获取系统配置"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return config.value if config else None


def set_config(db: Session, key: str, value: str, description: str = None):
    """设置系统配置"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if config:
        config.value = value
        if description:
            config.description = description
    else:
        config = SystemConfig(key=key, value=value, description=description)
        db.add(config)
    db.commit()


def get_notification_settings(db: Session) -> Dict[str, Any]:
    """获取通知设置"""
    settings_str = get_config(db, "notification_settings")
    if settings_str:
        try:
            return json.loads(settings_str)
        except:
            pass
    
    # 默认设置
    return {
        "enabled": False,
        "token_expiring_days": 7,      # Token 过期提前几天提醒
        "seat_warning_threshold": 80,  # 座位使用率预警阈值（百分比）
        "group_seat_warning_threshold": 5,  # 分组剩余座位预警阈值
        "notify_new_invite": True,     # 是否通知新邀请
        "notify_invite_accepted": False,  # 是否通知邀请接受
        "daily_report_enabled": False,    # 是否发送每日报告
        "daily_report_hour": 9,           # 每日报告发送时间（小时）
    }


def save_notification_settings(db: Session, settings: Dict[str, Any]):
    """保存通知设置"""
    set_config(db, "notification_settings", json.dumps(settings), "邮件通知设置")


def is_email_configured(db: Session) -> bool:
    """检查邮件是否已配置"""
    smtp_host = get_config(db, "smtp_host")
    smtp_port = get_config(db, "smtp_port")
    smtp_user = get_config(db, "smtp_user")
    smtp_password = get_config(db, "smtp_password")
    admin_email = get_config(db, "admin_email")
    return all([smtp_host, smtp_port, smtp_user, smtp_password, admin_email])


def send_email(
    db: Session,
    subject: str,
    content: str,
    to_email: Optional[str] = None
) -> bool:
    """发送邮件"""
    # 获取 SMTP 配置
    smtp_host = get_config(db, "smtp_host")
    smtp_port = get_config(db, "smtp_port")
    smtp_user = get_config(db, "smtp_user")
    smtp_password = get_config(db, "smtp_password")
    admin_email = to_email or get_config(db, "admin_email")
    
    if not all([smtp_host, smtp_port, smtp_user, smtp_password, admin_email]):
        logger.warning("Email not configured, skipping notification")
        return False
    
    try:
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = admin_email
        msg['Subject'] = f"[Team管理] {subject}"
        
        # HTML 内容
        html_content = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; background: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #1a1a2e; margin-bottom: 20px;">{subject}</h2>
                <div style="color: #333; line-height: 1.6;">
                    {content}
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">
                    此邮件由 ChatGPT Team 管理系统自动发送
                </p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # 发送邮件
        port = int(smtp_port)
        if port == 465:
            # SSL
            server = smtplib.SMTP_SSL(smtp_host, port, timeout=10)
        else:
            # TLS
            server = smtplib.SMTP(smtp_host, port, timeout=10)
            server.starttls()
        
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, admin_email, msg.as_string())
        server.quit()
        
        logger.info(f"Email sent: {subject} -> {admin_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def send_alert_email(db: Session, alerts: List[dict]) -> bool:
    """发送预警邮件"""
    if not alerts:
        return False
    
    # 检查通知是否启用
    settings = get_notification_settings(db)
    if not settings.get("enabled"):
        logger.info("Notifications disabled, skipping alert email")
        return False
    
    content_items = []
    for alert in alerts:
        alert_type = "🔴 严重" if alert.get("type") == "error" else "🟡 警告"
        bg_color = '#fee2e2' if alert.get('type') == 'error' else '#fef3c7'
        content_items.append(f"""
        <div style="padding: 15px; margin: 10px 0; background: {bg_color}; border-radius: 8px;">
            <strong>{alert_type}</strong> - <strong>{alert.get('team', '系统')}</strong><br>
            {alert.get('message', '')}
        </div>
        """)
    
    content = "".join(content_items)
    content += """
    <p style="margin-top: 20px;">
        <a href="#" style="display: inline-block; padding: 10px 20px; background: #1a1a2e; color: white; text-decoration: none; border-radius: 8px;">
            登录管理后台查看
        </a>
    </p>
    """
    
    return send_email(db, f"发现 {len(alerts)} 个预警", content)


def send_token_expiring_notification(db: Session, team_name: str, days_left: int) -> bool:
    """发送 Token 即将过期通知"""
    settings = get_notification_settings(db)
    if not settings.get("enabled"):
        return False
    
    if days_left <= 0:
        subject = f"⚠️ Token 已过期 - {team_name}"
        content = f"""
        <div style="padding: 20px; background: #fee2e2; border-radius: 8px; border-left: 4px solid #ef4444;">
            <h3 style="margin: 0 0 10px 0; color: #dc2626;">Token 已过期</h3>
            <p style="margin: 0;">Team <strong>{team_name}</strong> 的 Token 已过期，请尽快更新以恢复正常功能。</p>
        </div>
        """
    else:
        subject = f"⏰ Token 即将过期 - {team_name}"
        content = f"""
        <div style="padding: 20px; background: #fef3c7; border-radius: 8px; border-left: 4px solid #f59e0b;">
            <h3 style="margin: 0 0 10px 0; color: #d97706;">Token 即将过期</h3>
            <p style="margin: 0;">Team <strong>{team_name}</strong> 的 Token 将在 <strong>{days_left} 天</strong>后过期，请及时更新。</p>
        </div>
        """
    
    return send_email(db, subject, content)


def send_seat_warning_notification(db: Session, team_name: str, used: int, total: int) -> bool:
    """发送座位容量预警通知"""
    settings = get_notification_settings(db)
    if not settings.get("enabled"):
        return False
    
    percentage = round(used / total * 100) if total > 0 else 0
    
    if used >= total:
        subject = f"🚨 座位已满 - {team_name}"
        bg_color = "#fee2e2"
        border_color = "#ef4444"
        title_color = "#dc2626"
        title = "座位已满"
        message = f"Team <strong>{team_name}</strong> 的座位已满（{used}/{total}），无法继续邀请新成员。"
    else:
        subject = f"⚠️ 座位容量预警 - {team_name}"
        bg_color = "#fef3c7"
        border_color = "#f59e0b"
        title_color = "#d97706"
        title = "座位容量预警"
        message = f"Team <strong>{team_name}</strong> 的座位使用率已达 <strong>{percentage}%</strong>（{used}/{total}），请注意容量。"
    
    content = f"""
    <div style="padding: 20px; background: {bg_color}; border-radius: 8px; border-left: 4px solid {border_color};">
        <h3 style="margin: 0 0 10px 0; color: {title_color};">{title}</h3>
        <p style="margin: 0;">{message}</p>
        <div style="margin-top: 15px; background: #fff; border-radius: 4px; overflow: hidden;">
            <div style="height: 8px; background: {border_color}; width: {percentage}%;"></div>
        </div>
    </div>
    """
    
    return send_email(db, subject, content)


def send_new_invite_notification(db: Session, team_name: str, emails: List[str], success_count: int, fail_count: int) -> bool:
    """发送新邀请通知"""
    settings = get_notification_settings(db)
    if not settings.get("enabled") or not settings.get("notify_new_invite"):
        return False
    
    subject = f"📨 新邀请已发送 - {team_name}"
    
    email_list = "".join([f"<li>{email}</li>" for email in emails[:10]])
    if len(emails) > 10:
        email_list += f"<li>...还有 {len(emails) - 10} 个</li>"
    
    content = f"""
    <div style="padding: 20px; background: #ecfdf5; border-radius: 8px; border-left: 4px solid #10b981;">
        <h3 style="margin: 0 0 10px 0; color: #059669;">邀请已发送</h3>
        <p style="margin: 0 0 15px 0;">Team <strong>{team_name}</strong> 已发送 {len(emails)} 个邀请</p>
        <div style="display: flex; gap: 20px; margin-bottom: 15px;">
            <div style="padding: 10px 15px; background: #d1fae5; border-radius: 6px;">
                <span style="color: #059669; font-weight: bold;">{success_count}</span> 成功
            </div>
            <div style="padding: 10px 15px; background: #fee2e2; border-radius: 6px;">
                <span style="color: #dc2626; font-weight: bold;">{fail_count}</span> 失败
            </div>
        </div>
        <p style="margin: 0 0 5px 0; font-weight: bold;">邀请邮箱：</p>
        <ul style="margin: 0; padding-left: 20px; color: #666;">
            {email_list}
        </ul>
    </div>
    """
    
    return send_email(db, subject, content)


def send_daily_report(db: Session, stats: Dict[str, Any]) -> bool:
    """发送每日报告"""
    settings = get_notification_settings(db)
    if not settings.get("enabled") or not settings.get("daily_report_enabled"):
        return False
    
    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"📊 每日报告 - {today}"
    
    content = f"""
    <div style="padding: 20px; background: #f0f9ff; border-radius: 8px; border-left: 4px solid #0ea5e9;">
        <h3 style="margin: 0 0 20px 0; color: #0284c7;">每日数据报告</h3>
        
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">
            <div style="padding: 15px; background: white; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px; font-weight: bold; color: #1a1a2e;">{stats.get('total_teams', 0)}</div>
                <div style="color: #666; font-size: 14px;">Team 总数</div>
            </div>
            <div style="padding: 15px; background: white; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px; font-weight: bold; color: #1a1a2e;">{stats.get('total_members', 0)}</div>
                <div style="color: #666; font-size: 14px;">成员总数</div>
            </div>
            <div style="padding: 15px; background: white; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px; font-weight: bold; color: #10b981;">{stats.get('invites_today', 0)}</div>
                <div style="color: #666; font-size: 14px;">今日邀请</div>
            </div>
            <div style="padding: 15px; background: white; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px; font-weight: bold; color: #f59e0b;">{stats.get('pending_invites', 0)}</div>
                <div style="color: #666; font-size: 14px;">待接受邀请</div>
            </div>
        </div>
        
        <div style="padding: 15px; background: white; border-radius: 8px;">
            <h4 style="margin: 0 0 10px 0; color: #333;">座位使用情况</h4>
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>已使用</span>
                <span>{stats.get('used_seats', 0)} / {stats.get('total_seats', 0)}</span>
            </div>
            <div style="background: #e5e7eb; border-radius: 4px; overflow: hidden;">
                <div style="height: 8px; background: #10b981; width: {stats.get('seat_usage_percent', 0)}%;"></div>
            </div>
        </div>
    </div>
    """
    
    return send_email(db, subject, content)


def send_group_seat_warning(db: Session, group_name: str, used: int, total: int, available: int) -> bool:
    """发送分组座位预警通知"""
    settings = get_notification_settings(db)
    if not settings.get("enabled"):
        return False
    
    percentage = round(used / total * 100) if total > 0 else 0
    
    if available <= 0:
        subject = f"🚨 分组座位已满 - {group_name}"
        bg_color = "#fee2e2"
        border_color = "#ef4444"
        title_color = "#dc2626"
        title = "分组座位已满"
        message = f"分组 <strong>{group_name}</strong> 的座位已全部占用（{used}/{total}），无法继续邀请新成员！"
    elif available <= 3:
        subject = f"⚠️ 分组座位即将满 - {group_name}"
        bg_color = "#fef3c7"
        border_color = "#f59e0b"
        title_color = "#d97706"
        title = "分组座位即将满"
        message = f"分组 <strong>{group_name}</strong> 仅剩 <strong>{available}</strong> 个空位（{used}/{total}），请及时处理。"
    else:
        subject = f"📊 分组座位预警 - {group_name}"
        bg_color = "#fef3c7"
        border_color = "#f59e0b"
        title_color = "#d97706"
        title = "分组座位预警"
        message = f"分组 <strong>{group_name}</strong> 座位使用率已达 <strong>{percentage}%</strong>（{used}/{total}），剩余 {available} 个空位。"
    
    content = f"""
    <div style="padding: 20px; background: {bg_color}; border-radius: 8px; border-left: 4px solid {border_color};">
        <h3 style="margin: 0 0 10px 0; color: {title_color};">{title}</h3>
        <p style="margin: 0;">{message}</p>
        <div style="margin-top: 15px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 14px;">
                <span>座位使用情况</span>
                <span>{used} / {total} (剩余 {available})</span>
            </div>
            <div style="background: #fff; border-radius: 4px; overflow: hidden;">
                <div style="height: 10px; background: {border_color}; width: {percentage}%;"></div>
            </div>
        </div>
    </div>
    """
    
    return send_email(db, subject, content)


def test_email_connection(db: Session) -> Dict[str, Any]:
    """测试邮件连接"""
    smtp_host = get_config(db, "smtp_host")
    smtp_port = get_config(db, "smtp_port")
    smtp_user = get_config(db, "smtp_user")
    smtp_password = get_config(db, "smtp_password")
    
    if not all([smtp_host, smtp_port, smtp_user, smtp_password]):
        return {"success": False, "message": "SMTP 配置不完整"}
    
    try:
        port = int(smtp_port)
        if port == 465:
            server = smtplib.SMTP_SSL(smtp_host, port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_host, port, timeout=10)
            server.starttls()
        
        server.login(smtp_user, smtp_password)
        server.quit()
        
        return {"success": True, "message": "SMTP 连接成功"}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}
