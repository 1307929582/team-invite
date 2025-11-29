# Pydantic Schemas
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.models import UserRole, InviteStatus


# ========== Auth ==========
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.VIEWER


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Team ==========
class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None
    account_id: str
    session_token: str
    device_id: Optional[str] = None
    cookie: Optional[str] = None
    group_id: Optional[int] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    session_token: Optional[str] = None
    device_id: Optional[str] = None
    cookie: Optional[str] = None
    is_active: Optional[bool] = None
    group_id: Optional[int] = None


class TeamResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    account_id: str
    is_active: bool
    max_seats: int = 5
    token_expires_at: Optional[datetime]
    created_at: datetime
    member_count: Optional[int] = 0
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class TeamListResponse(BaseModel):
    teams: List[TeamResponse]
    total: int


# ========== Team Member ==========
class TeamMemberResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    role: str
    chatgpt_user_id: Optional[str]
    joined_at: Optional[datetime]
    synced_at: datetime
    
    class Config:
        from_attributes = True


class TeamMemberListResponse(BaseModel):
    members: List[TeamMemberResponse]
    total: int
    team_name: str


# ========== Invite ==========
class InviteRequest(BaseModel):
    emails: List[EmailStr]


class InviteResult(BaseModel):
    email: str
    success: bool
    error: Optional[str] = None


class BatchInviteResponse(BaseModel):
    batch_id: str
    total: int
    success_count: int
    fail_count: int
    results: List[InviteResult]


class InviteRecordResponse(BaseModel):
    id: int
    email: str
    status: InviteStatus
    error_message: Optional[str]
    batch_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Operation Log ==========
class OperationLogResponse(BaseModel):
    id: int
    action: str
    target: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    user_name: Optional[str] = None
    team_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class OperationLogListResponse(BaseModel):
    logs: List[OperationLogResponse]
    total: int


# ========== Dashboard ==========
class DashboardStats(BaseModel):
    total_teams: int
    total_members: int
    invites_today: int
    invites_this_week: int
    active_teams: int


# ========== Common ==========
class MessageResponse(BaseModel):
    message: str
    success: bool = True
