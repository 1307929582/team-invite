# API 限流配置
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse


def get_real_ip(request: Request) -> str:
    """获取真实 IP（支持反向代理）"""
    # 优先从 X-Forwarded-For 获取
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # 取第一个 IP（客户端真实 IP）
        return forwarded.split(",")[0].strip()
    
    # 其次从 X-Real-IP 获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 最后使用直连 IP
    return get_remote_address(request)


# 创建限流器
limiter = Limiter(key_func=get_real_ip)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """限流超出处理"""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "请求过于频繁，请稍后再试",
            "retry_after": exc.detail
        }
    )
