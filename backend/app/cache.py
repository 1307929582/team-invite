# Redis 缓存服务
import json
import os
import logging
from typing import Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Redis 客户端（延迟初始化）
_redis_client = None


def get_redis():
    """获取 Redis 客户端"""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            _redis_client.ping()
            logger.info(f"Redis connected: {REDIS_URL}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, caching disabled")
            _redis_client = None
    return _redis_client


class CacheKeys:
    """缓存键定义"""
    SUBSCRIPTION = "subscription:{team_id}"
    PENDING_INVITES = "pending_invites:{team_id}"
    MEMBERS = "members:{team_id}"
    ALL_PENDING_INVITES = "all_pending_invites"


class CacheTTL:
    """缓存过期时间（秒）"""
    SUBSCRIPTION = 600  # 10 分钟
    PENDING_INVITES = 300  # 5 分钟
    MEMBERS = 300  # 5 分钟


def cache_get(key: str) -> Optional[Any]:
    """从缓存获取数据"""
    client = get_redis()
    if not client:
        return None
    try:
        data = client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Cache get error: {e}")
    return None


def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """设置缓存数据"""
    client = get_redis()
    if not client:
        return False
    try:
        client.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as e:
        logger.warning(f"Cache set error: {e}")
    return False


def cache_delete(key: str) -> bool:
    """删除缓存"""
    client = get_redis()
    if not client:
        return False
    try:
        client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete error: {e}")
    return False


def cache_delete_pattern(pattern: str) -> int:
    """删除匹配模式的所有缓存"""
    client = get_redis()
    if not client:
        return 0
    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
    except Exception as e:
        logger.warning(f"Cache delete pattern error: {e}")
    return 0


# Team 相关缓存操作
def get_subscription_cache(team_id: int) -> Optional[dict]:
    key = CacheKeys.SUBSCRIPTION.format(team_id=team_id)
    return cache_get(key)


def set_subscription_cache(team_id: int, data: dict):
    key = CacheKeys.SUBSCRIPTION.format(team_id=team_id)
    cache_set(key, data, CacheTTL.SUBSCRIPTION)


def get_pending_invites_cache(team_id: int) -> Optional[dict]:
    key = CacheKeys.PENDING_INVITES.format(team_id=team_id)
    return cache_get(key)


def set_pending_invites_cache(team_id: int, data: dict):
    key = CacheKeys.PENDING_INVITES.format(team_id=team_id)
    cache_set(key, data, CacheTTL.PENDING_INVITES)


def get_members_cache(team_id: int) -> Optional[list]:
    key = CacheKeys.MEMBERS.format(team_id=team_id)
    return cache_get(key)


def set_members_cache(team_id: int, data: list):
    key = CacheKeys.MEMBERS.format(team_id=team_id)
    cache_set(key, data, CacheTTL.MEMBERS)


def invalidate_team_cache(team_id: int):
    """清除指定 Team 的所有缓存"""
    cache_delete(CacheKeys.SUBSCRIPTION.format(team_id=team_id))
    cache_delete(CacheKeys.PENDING_INVITES.format(team_id=team_id))
    cache_delete(CacheKeys.MEMBERS.format(team_id=team_id))
    cache_delete(CacheKeys.ALL_PENDING_INVITES)


def invalidate_all_cache():
    """清除所有缓存"""
    cache_delete_pattern("subscription:*")
    cache_delete_pattern("pending_invites:*")
    cache_delete_pattern("members:*")
    cache_delete(CacheKeys.ALL_PENDING_INVITES)
