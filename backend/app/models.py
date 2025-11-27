# 数据库模型
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class InviteStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class User(Base):
    """系统用户（管理平台的用户）"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    operation_logs = relationship("OperationLog", back_populates="user")


class Team(Base):
    """ChatGPT Team 配置"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    account_id = Column(String(100), nullable=False)
    session_token = Column(Text, nullable=False)
    device_id = Column(String(100), nullable=True)
    cookie = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    max_seats = Column(Integer, default=5)  # 最大座位数
    group_id = Column(Integer, ForeignKey("team_groups.id"), nullable=True)  # 所属分组
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    group = relationship("TeamGroup", back_populates="teams")
    members = relationship("TeamMember", back_populates="team")
    invites = relationship("InviteRecord", back_populates="team")
    operation_logs = relationship("OperationLog", back_populates="team")


class TeamMember(Base):
    """Team 成员缓存"""
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    email = Column(String(100), nullable=False)
    name = Column(String(100), nullable=True)
    role = Column(String(50), default="member")
    chatgpt_user_id = Column(String(100), nullable=True)
    joined_at = Column(DateTime, nullable=True)
    synced_at = Column(DateTime, default=datetime.utcnow)
    
    team = relationship("Team", back_populates="members")


class InviteRecord(Base):
    """邀请记录"""
    __tablename__ = "invite_records"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    email = Column(String(100), nullable=False)
    linuxdo_user_id = Column(Integer, ForeignKey("linuxdo_users.id"), nullable=True)
    status = Column(Enum(InviteStatus), default=InviteStatus.PENDING)
    error_message = Column(Text, nullable=True)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    redeem_code = Column(String(50), nullable=True)
    batch_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)  # 接受邀请时间
    
    team = relationship("Team", back_populates="invites")
    linuxdo_user = relationship("LinuxDOUser", back_populates="invites")


class OperationLog(Base):
    """操作日志"""
    __tablename__ = "operation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    action = Column(String(50), nullable=False)
    target = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="operation_logs")
    team = relationship("Team", back_populates="operation_logs")


class TeamGroup(Base):
    """Team 分组"""
    __tablename__ = "team_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    color = Column(String(20), default="#1890ff")  # 标签颜色
    created_at = Column(DateTime, default=datetime.utcnow)
    
    teams = relationship("Team", back_populates="group")
    redeem_codes = relationship("RedeemCode", back_populates="group")


class RedeemCodeType(str, enum.Enum):
    LINUXDO = "linuxdo"  # 需要 LinuxDO 登录
    DIRECT = "direct"    # 直接链接，无需登录


class RedeemCode(Base):
    """兑换码"""
    __tablename__ = "redeem_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    code_type = Column(Enum(RedeemCodeType), default=RedeemCodeType.LINUXDO)
    max_uses = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    note = Column(String(255), nullable=True)  # 备注/订单号
    group_id = Column(Integer, ForeignKey("team_groups.id"), nullable=True)  # 绑定分组
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    group = relationship("TeamGroup", back_populates="redeem_codes")


class LinuxDOUser(Base):
    """LinuxDO 用户"""
    __tablename__ = "linuxdo_users"
    
    id = Column(Integer, primary_key=True, index=True)
    linuxdo_id = Column(String(100), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    trust_level = Column(Integer, default=0)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    
    invites = relationship("InviteRecord", back_populates="linuxdo_user")


class SystemConfig(Base):
    """系统配置（存储 LinuxDO OAuth 等配置）"""
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InviteQueueStatus(str, enum.Enum):
    PENDING = "pending"      # 等待发送
    PROCESSING = "processing"  # 正在处理
    SUCCESS = "success"      # 发送成功
    FAILED = "failed"        # 发送失败


class InviteQueue(Base):
    """邀请队列（超过每日限制的邀请进入队列）"""
    __tablename__ = "invite_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), nullable=False)
    redeem_code = Column(String(50), nullable=True)
    linuxdo_user_id = Column(Integer, ForeignKey("linuxdo_users.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("team_groups.id"), nullable=True)  # 指定分组
    status = Column(Enum(InviteQueueStatus), default=InviteQueueStatus.PENDING)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    linuxdo_user = relationship("LinuxDOUser")
    group = relationship("TeamGroup")


# ==================== Gemini Business 模块 ====================

class GeminiTeam(Base):
    """Gemini Business Team 配置"""
    __tablename__ = "gemini_teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    account_id = Column(String(100), nullable=False)  # Gemini 账户 ID
    cookies = Column(Text, nullable=False)  # 完整的 cookie 字符串
    max_seats = Column(Integer, default=10)  # 最大座位数
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    members = relationship("GeminiMember", back_populates="team", cascade="all, delete-orphan")
    invites = relationship("GeminiInviteRecord", back_populates="team", cascade="all, delete-orphan")


class GeminiMember(Base):
    """Gemini Team 成员缓存"""
    __tablename__ = "gemini_members"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("gemini_teams.id"), nullable=False)
    email = Column(String(100), nullable=False)
    role = Column(String(50), default="viewer")  # viewer 或 admin
    gemini_member_id = Column(Integer, nullable=True)  # Gemini 内部成员 ID
    synced_at = Column(DateTime, default=datetime.utcnow)
    
    team = relationship("GeminiTeam", back_populates="members")


class GeminiInviteRecord(Base):
    """Gemini 邀请记录"""
    __tablename__ = "gemini_invite_records"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("gemini_teams.id"), nullable=False)
    email = Column(String(100), nullable=False)
    role = Column(String(50), default="viewer")
    status = Column(String(20), default="pending")  # 使用 String 避免枚举冲突
    error_message = Column(Text, nullable=True)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    team = relationship("GeminiTeam", back_populates="invites")
