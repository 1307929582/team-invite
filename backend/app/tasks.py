# 异步任务队列 - 批量处理版
import asyncio
import logging
from typing import Optional, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# 邀请队列
_invite_queue: asyncio.Queue = None
_worker_task: asyncio.Task = None

# 批量处理配置
BATCH_SIZE = 10  # 每批处理数量
BATCH_INTERVAL = 3  # 批次间隔秒数


async def get_invite_queue() -> asyncio.Queue:
    global _invite_queue
    if _invite_queue is None:
        _invite_queue = asyncio.Queue(maxsize=5000)
    return _invite_queue


async def enqueue_invite(email: str, redeem_code: str, group_id: int = None, linuxdo_user_id: int = None) -> str:
    """添加邀请到队列，返回队列 ID"""
    queue = await get_invite_queue()
    queue_id = f"q-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{queue.qsize()}"
    
    task = {
        "queue_id": queue_id,
        "email": email.lower().strip(),
        "redeem_code": redeem_code,
        "group_id": group_id,
        "linuxdo_user_id": linuxdo_user_id,
        "created_at": datetime.utcnow()
    }
    
    try:
        queue.put_nowait(task)
        logger.info(f"Invite enqueued: {email}, queue size: {queue.qsize()}")
        return queue_id
    except asyncio.QueueFull:
        logger.warning(f"Invite queue full!")
        raise Exception("系统繁忙，请稍后再试")


async def get_queue_status() -> dict:
    """获取队列状态"""
    queue = await get_invite_queue()
    return {
        "queue_size": queue.qsize(),
        "max_size": 5000,
        "batch_size": BATCH_SIZE,
        "batch_interval": BATCH_INTERVAL
    }


async def process_invite_batch(batch: List[Dict]):
    """批量处理邀请"""
    from app.services.chatgpt_api import ChatGPTAPI, ChatGPTAPIError
    from app.database import SessionLocal
    from app.models import Team, TeamMember, InviteRecord, InviteStatus, OperationLog, TeamGroup, InviteQueue, InviteQueueStatus
    from app.cache import invalidate_seat_cache
    from sqlalchemy import func
    
    if not batch:
        return
    
    db = SessionLocal()
    try:
        # 按 group_id 分组
        groups: Dict[int, List[Dict]] = {}
        for item in batch:
            gid = item.get("group_id") or 0
            if gid not in groups:
                groups[gid] = []
            groups[gid].append(item)
        
        for group_id, items in groups.items():
            # 找到该分组有空位的 Team
            team_query = db.query(Team).filter(Team.is_active == True)
            if group_id:
                team_query = team_query.filter(Team.group_id == group_id)
            
            # 子查询统计成员数
            member_count_subq = db.query(
                TeamMember.team_id,
                func.count(TeamMember.id).label('member_count')
            ).group_by(TeamMember.team_id).subquery()
            
            available_team = team_query.outerjoin(
                member_count_subq,
                Team.id == member_count_subq.c.team_id
            ).filter(
                func.coalesce(member_count_subq.c.member_count, 0) < Team.max_seats
            ).first()
            
            if not available_team:
                # 没有空位，标记失败
                for item in items:
                    record = InviteQueue(
                        email=item["email"],
                        redeem_code=item.get("redeem_code"),
                        linuxdo_user_id=item.get("linuxdo_user_id"),
                        group_id=group_id if group_id else None,
                        status=InviteQueueStatus.FAILED,
                        error_message="所有 Team 已满",
                        processed_at=datetime.utcnow()
                    )
                    db.add(record)
                db.commit()
                logger.warning(f"No available team for group {group_id}")
                continue
            
            # 批量邀请
            emails = [item["email"] for item in items]
            try:
                api = ChatGPTAPI(available_team.session_token, available_team.device_id or "")
                await api.invite_members(available_team.account_id, emails)
                
                # 记录成功
                for item in items:
                    invite = InviteRecord(
                        team_id=available_team.id,
                        email=item["email"],
                        linuxdo_user_id=item.get("linuxdo_user_id"),
                        status=InviteStatus.SUCCESS,
                        redeem_code=item.get("redeem_code"),
                        batch_id=f"batch-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                    )
                    db.add(invite)
                
                db.commit()
                invalidate_seat_cache()
                logger.info(f"Batch invite success: {len(emails)} emails to {available_team.name}")
                
                # 发送 Telegram 通知（批量）
                await send_batch_telegram_notify(db, emails, available_team.name)
                
            except ChatGPTAPIError as e:
                logger.error(f"Batch invite failed: {e.message}")
                # 批量失败，逐个重试
                for item in items:
                    try:
                        await api.invite_members(available_team.account_id, [item["email"]])
                        invite = InviteRecord(
                            team_id=available_team.id,
                            email=item["email"],
                            linuxdo_user_id=item.get("linuxdo_user_id"),
                            status=InviteStatus.SUCCESS,
                            redeem_code=item.get("redeem_code"),
                            batch_id=f"retry-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                        )
                        db.add(invite)
                    except Exception as e2:
                        invite = InviteRecord(
                            team_id=available_team.id,
                            email=item["email"],
                            linuxdo_user_id=item.get("linuxdo_user_id"),
                            status=InviteStatus.FAILED,
                            redeem_code=item.get("redeem_code"),
                            error_message=str(e2)[:200]
                        )
                        db.add(invite)
                    await asyncio.sleep(0.5)
                db.commit()
                
    except Exception as e:
        logger.error(f"Process batch error: {e}")
    finally:
        db.close()


async def send_batch_telegram_notify(db, emails: List[str], team_name: str):
    """批量发送 Telegram 通知"""
    from app.models import SystemConfig
    from app.services.telegram import send_telegram_message
    
    try:
        def get_cfg(key):
            c = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            return c.value if c else None
        
        if get_cfg("telegram_enabled") != "true" or get_cfg("telegram_notify_invite") != "true":
            return
        
        bot_token = get_cfg("telegram_bot_token")
        chat_id = get_cfg("telegram_chat_id")
        if not bot_token or not chat_id:
            return
        
        msg = f"🎉 <b>批量上车成功</b>\n\n👥 Team: {team_name}\n📧 人数: {len(emails)}\n\n"
        if len(emails) <= 5:
            msg += "\n".join([f"• <code>{e}</code>" for e in emails])
        else:
            msg += "\n".join([f"• <code>{e}</code>" for e in emails[:5]])
            msg += f"\n... 等 {len(emails)} 人"
        
        await send_telegram_message(bot_token, chat_id, msg)
    except Exception as e:
        logger.warning(f"Telegram batch notify failed: {e}")


async def invite_worker():
    """邀请处理 worker - 批量处理"""
    queue = await get_invite_queue()
    logger.info("Invite worker started (batch mode)")
    
    while True:
        try:
            batch = []
            
            # 收集一批任务
            try:
                # 等待第一个任务
                first = await asyncio.wait_for(queue.get(), timeout=BATCH_INTERVAL)
                batch.append(first)
                queue.task_done()
                
                # 快速收集更多（不等待）
                while len(batch) < BATCH_SIZE:
                    try:
                        item = queue.get_nowait()
                        batch.append(item)
                        queue.task_done()
                    except asyncio.QueueEmpty:
                        break
                        
            except asyncio.TimeoutError:
                # 超时没有新任务，继续等待
                continue
            
            if batch:
                logger.info(f"Processing batch of {len(batch)} invites")
                await process_invite_batch(batch)
                
            # 批次间隔
            await asyncio.sleep(1)
            
        except asyncio.CancelledError:
            logger.info("Invite worker cancelled")
            break
        except Exception as e:
            logger.error(f"Invite worker error: {e}")
            await asyncio.sleep(1)


async def start_task_worker():
    """启动任务 worker"""
    global _worker_task
    if _worker_task is None or _worker_task.done():
        _worker_task = asyncio.create_task(invite_worker())
        logger.info("Invite worker started")


async def stop_task_worker():
    """停止任务 worker"""
    global _worker_task
    if _worker_task and not _worker_task.done():
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
        logger.info("Invite worker stopped")
