# Team 管理路由
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Team, TeamMember, User, TeamGroup
from app.schemas import (
    TeamCreate, TeamUpdate, TeamResponse, TeamListResponse,
    TeamMemberResponse, TeamMemberListResponse, MessageResponse
)
from app.services.auth import get_current_user
from app.services.chatgpt_api import ChatGPTAPI, ChatGPTAPIError

router = APIRouter(prefix="/teams", tags=["Team 管理"])


@router.get("", response_model=TeamListResponse)
async def list_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有 Team 列表"""
    teams = db.query(Team).filter(Team.is_active == True).all()
    
    # 获取分组名称映射
    group_ids = [t.group_id for t in teams if t.group_id]
    groups = {}
    if group_ids:
        group_list = db.query(TeamGroup).filter(TeamGroup.id.in_(group_ids)).all()
        groups = {g.id: g.name for g in group_list}
    
    result = []
    for team in teams:
        member_count = db.query(TeamMember).filter(TeamMember.team_id == team.id).count()
        team_dict = TeamResponse.model_validate(team).model_dump()
        team_dict["member_count"] = member_count
        team_dict["group_id"] = team.group_id
        team_dict["group_name"] = groups.get(team.group_id) if team.group_id else None
        result.append(TeamResponse(**team_dict))
    
    return TeamListResponse(teams=result, total=len(result))


@router.post("", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新 Team"""
    # 自动清理空格
    clean_data = team_data.model_dump()
    clean_data["account_id"] = clean_data["account_id"].strip()
    clean_data["session_token"] = clean_data["session_token"].strip()
    if clean_data.get("device_id"):
        clean_data["device_id"] = clean_data["device_id"].strip()
    
    # 验证 Token 是否有效
    try:
        api = ChatGPTAPI(clean_data["session_token"], clean_data.get("device_id") or "")
        await api.verify_token()
    except ChatGPTAPIError as e:
        raise HTTPException(status_code=400, detail=f"Token 验证失败: {e.message}")
    
    # 检查是否已存在（只检查活跃的）
    existing = db.query(Team).filter(
        Team.account_id == clean_data["account_id"],
        Team.is_active == True
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该 Account 已存在")
    
    team = Team(**clean_data)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 Team 详情"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    member_count = db.query(TeamMember).filter(TeamMember.team_id == team.id).count()
    team_dict = TeamResponse.model_validate(team).model_dump()
    team_dict["member_count"] = member_count
    return TeamResponse(**team_dict)


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    team_data: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新 Team 配置"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    update_data = team_data.model_dump(exclude_unset=True)
    
    # 自动清理空格
    if "session_token" in update_data:
        update_data["session_token"] = update_data["session_token"].strip()
    if "device_id" in update_data:
        update_data["device_id"] = update_data["device_id"].strip()
    if "account_id" in update_data:
        update_data["account_id"] = update_data["account_id"].strip()
    
    if update_data.get("session_token"):
        try:
            api = ChatGPTAPI(update_data["session_token"], update_data.get("device_id") or team.device_id or "")
            await api.verify_token()
        except ChatGPTAPIError as e:
            raise HTTPException(status_code=400, detail=f"Token 验证失败: {e.message}")
    
    for key, value in update_data.items():
        setattr(team, key, value)
    
    db.commit()
    db.refresh(team)
    return team


@router.delete("/{team_id}", response_model=MessageResponse)
async def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除 Team"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    team.is_active = False
    db.commit()
    return MessageResponse(message="Team 已删除")


@router.get("/{team_id}/members", response_model=TeamMemberListResponse)
async def get_team_members(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 Team 成员列表（从缓存）"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    return TeamMemberListResponse(
        members=[TeamMemberResponse.model_validate(m) for m in members],
        total=len(members),
        team_name=team.name
    )


@router.post("/{team_id}/sync", response_model=TeamMemberListResponse)
async def sync_team_members(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从 ChatGPT 同步成员列表"""
    from app.models import InviteRecord, InviteStatus
    
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    try:
        api = ChatGPTAPI(team.session_token, team.device_id or "", team.cookie or "")
        result = await api.get_members(team.account_id)
        members_data = result.get("items", result.get("users", []))
    except ChatGPTAPIError as e:
        raise HTTPException(status_code=400, detail=f"同步失败: {e.message}")
    
    # 获取成员邮箱列表
    from datetime import datetime
    member_emails = set()
    for m in members_data:
        email = m.get("email", "").lower().strip()
        if email:
            member_emails.add(email)
    
    print(f"[Sync] Team {team.name}: 成员邮箱列表 = {member_emails}")
    
    # 更新邀请记录：如果邮箱已在成员列表中，标记为已接受
    pending_invites = db.query(InviteRecord).filter(
        InviteRecord.team_id == team_id,
        InviteRecord.status == InviteStatus.SUCCESS,
        InviteRecord.accepted_at == None
    ).all()
    
    print(f"[Sync] Team {team.name}: 待接受邀请 = {[(i.id, i.email) for i in pending_invites]}")
    
    updated_count = 0
    for invite in pending_invites:
        invite_email = invite.email.lower().strip()
        print(f"[Sync] 检查邀请 {invite.id}: '{invite_email}' in member_emails = {invite_email in member_emails}")
        if invite_email in member_emails:
            invite.accepted_at = datetime.utcnow()
            updated_count += 1
    
    print(f"[Sync] Team {team.name}: 更新了 {updated_count} 条邀请记录")
    
    # 清除旧成员数据
    db.query(TeamMember).filter(TeamMember.team_id == team_id).delete()
    
    # 插入新成员数据（去重）
    seen_emails = set()
    for m in members_data:
        email = m.get("email", "").lower().strip()
        if not email or email in seen_emails:
            continue
        seen_emails.add(email)
        
        member = TeamMember(
            team_id=team_id,
            email=email,
            name=m.get("name", m.get("display_name", "")),
            role=m.get("role", "member"),
            chatgpt_user_id=m.get("id", m.get("user_id", "")),
            synced_at=datetime.utcnow()
        )
        db.add(member)
    
    db.commit()
    
    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    return TeamMemberListResponse(
        members=[TeamMemberResponse.model_validate(m) for m in members],
        total=len(members),
        team_name=team.name
    )


@router.post("/{team_id}/verify-token", response_model=MessageResponse)
async def verify_team_token(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """验证 Team Token 是否有效"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    try:
        api = ChatGPTAPI(team.session_token, team.device_id or "", team.cookie or "")
        await api.verify_token()
        return MessageResponse(message="Token 有效")
    except ChatGPTAPIError as e:
        raise HTTPException(status_code=400, detail=f"Token 无效: {e.message}")


@router.get("/{team_id}/subscription")
async def get_team_subscription(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 Team 订阅信息"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    try:
        api = ChatGPTAPI(team.session_token, team.device_id or "", team.cookie or "")
        return await api.get_subscription(team.account_id)
    except ChatGPTAPIError as e:
        raise HTTPException(status_code=400, detail=f"获取失败: {e.message}")


@router.get("/{team_id}/pending-invites")
async def get_pending_invites(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取待处理的邀请"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team 不存在")
    
    try:
        api = ChatGPTAPI(team.session_token, team.device_id or "", team.cookie or "")
        return await api.get_invites(team.account_id)
    except ChatGPTAPIError as e:
        raise HTTPException(status_code=400, detail=f"获取失败: {e.message}")


@router.post("/sync-all", response_model=MessageResponse)
async def sync_all_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量同步所有 Team 成员"""
    from datetime import datetime
    from app.models import InviteRecord, InviteStatus
    import asyncio
    
    teams_list = db.query(Team).filter(Team.is_active == True).all()
    success_count = 0
    fail_count = 0
    
    for team in teams_list:
        try:
            api = ChatGPTAPI(team.session_token, team.device_id or "", team.cookie or "")
            result = await api.get_members(team.account_id)
            members_data = result.get("items", result.get("users", []))
            
            # 获取成员邮箱列表
            member_emails = set()
            for m in members_data:
                email = m.get("email", "").lower().strip()
                if email:
                    member_emails.add(email)
            
            # 更新邀请记录
            pending_invites = db.query(InviteRecord).filter(
                InviteRecord.team_id == team.id,
                InviteRecord.status == InviteStatus.SUCCESS,
                InviteRecord.accepted_at == None
            ).all()
            
            for invite in pending_invites:
                if invite.email.lower().strip() in member_emails:
                    invite.accepted_at = datetime.utcnow()
            
            # 清除旧成员数据
            db.query(TeamMember).filter(TeamMember.team_id == team.id).delete()
            
            # 插入新成员数据（去重）
            seen_emails = set()
            for m in members_data:
                email = m.get("email", "").lower().strip()
                if not email or email in seen_emails:
                    continue
                seen_emails.add(email)
                
                member = TeamMember(
                    team_id=team.id,
                    email=email,
                    name=m.get("name", m.get("display_name", "")),
                    role=m.get("role", "member"),
                    chatgpt_user_id=m.get("id", m.get("user_id", "")),
                    synced_at=datetime.utcnow()
                )
                db.add(member)
            
            db.commit()
            success_count += 1
            
        except Exception:
            fail_count += 1
        
        # 每个 Team 间隔 1 秒
        await asyncio.sleep(1)
    
    return MessageResponse(message=f"同步完成：成功 {success_count} 个，失败 {fail_count} 个")
