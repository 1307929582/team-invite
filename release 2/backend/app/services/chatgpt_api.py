# ChatGPT API 封装 - 基于真实接口
import httpx
import asyncio
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

API_BASE = "https://chatgpt.com/backend-api"


class ChatGPTAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")


class ChatGPTAPI:
    """ChatGPT API 客户端"""
    
    def __init__(self, session_token: str, device_id: str = "", cookie: str = ""):
        self.session_token = session_token
        self.device_id = device_id
        self.cookie = cookie
        
    def _get_headers(self, account_id: str = "") -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.session_token.strip()}",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Origin": "https://chatgpt.com",
            "Referer": "https://chatgpt.com/admin/members",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "oai-language": "zh-CN",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }
        
        if self.device_id:
            headers["oai-device-id"] = self.device_id.strip()
            
        if account_id:
            headers["chatgpt-account-id"] = account_id.strip()
            
        if self.cookie:
            # 清理换行符和多余空格
            clean_cookie = self.cookie.replace('\n', '').replace('\r', '').strip()
            headers["Cookie"] = clean_cookie
            
        return headers
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        account_id: str = "",
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        url = f"{API_BASE}{endpoint}"
        headers = self._get_headers(account_id)
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                )
                
                logger.info(f"Request: {method} {url} -> {response.status_code}")
                
                if response.status_code == 401:
                    raise ChatGPTAPIError(401, "Token 已过期，请更新")
                elif response.status_code == 403:
                    raise ChatGPTAPIError(403, f"无权限访问: {response.text[:200]}")
                elif response.status_code == 429:
                    raise ChatGPTAPIError(429, "请求过于频繁，请稍后再试")
                elif response.status_code >= 400:
                    raise ChatGPTAPIError(response.status_code, response.text[:200])
                
                return response.json()
                
            except httpx.TimeoutException:
                raise ChatGPTAPIError(408, "请求超时")
            except httpx.RequestError as e:
                raise ChatGPTAPIError(500, f"网络错误: {str(e)}")
    
    async def verify_token(self) -> Dict[str, Any]:
        """验证 Token"""
        return await self._request("GET", "/me")
    
    async def get_members(self, account_id: str, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        """获取 Team 成员列表"""
        params = {"offset": offset, "limit": limit, "query": ""}
        return await self._request("GET", f"/accounts/{account_id}/users", account_id, params=params)
    
    async def invite_members(
        self, 
        account_id: str, 
        emails: List[str], 
        role: str = "standard-user",
        resend: bool = True
    ) -> Dict[str, Any]:
        """邀请成员"""
        data = {
            "email_addresses": emails,
            "role": role,
            "resend_emails": resend
        }
        return await self._request("POST", f"/accounts/{account_id}/invites", account_id, data=data)
    
    async def get_invites(self, account_id: str) -> Dict[str, Any]:
        """获取待处理的邀请列表"""
        return await self._request("GET", f"/accounts/{account_id}/invites", account_id)
    
    async def get_subscription(self, account_id: str) -> Dict[str, Any]:
        """获取订阅信息（座位数、到期时间等）"""
        params = {"account_id": account_id}
        return await self._request("GET", "/subscriptions", account_id, params=params)
    
    async def get_identity(self, account_id: str) -> Dict[str, Any]:
        """获取账户身份信息"""
        return await self._request("GET", f"/accounts/{account_id}/identity", account_id)


async def batch_invite(
    api: ChatGPTAPI,
    account_id: str,
    emails: List[str],
    batch_size: int = 10,
    delay: float = 1.0
) -> List[Dict[str, Any]]:
    """批量邀请成员"""
    results = []
    
    for i in range(0, len(emails), batch_size):
        batch = emails[i:i + batch_size]
        
        try:
            await api.invite_members(account_id, batch)
            for email in batch:
                results.append({"email": email, "success": True, "error": None})
            logger.info(f"Successfully invited batch: {batch}")
        except ChatGPTAPIError as e:
            logger.warning(f"Batch invite failed: {e.message}")
            for email in batch:
                try:
                    await api.invite_members(account_id, [email])
                    results.append({"email": email, "success": True, "error": None})
                except ChatGPTAPIError as e2:
                    results.append({"email": email, "success": False, "error": e2.message})
                await asyncio.sleep(0.5)
        
        if i + batch_size < len(emails):
            await asyncio.sleep(delay)
    
    return results
