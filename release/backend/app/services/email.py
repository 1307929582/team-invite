# 邮件通知服务
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models import SystemConfig
from app.logger import get_logger

logger = get_logger(__name__)


def get_config(db: Session, key: str) -> Optional[str]:
    """获取系统配置"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return config.value if config else None


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
    
    content_items = []
    for alert in alerts:
        alert_type = "🔴 严重" if alert.get("type") == "error" else "🟡 警告"
        content_items.append(f"""
        <div style="padding: 15px; margin: 10px 0; background: {'#fee2e2' if alert.get('type') == 'error' else '#fef3c7'}; border-radius: 8px;">
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
