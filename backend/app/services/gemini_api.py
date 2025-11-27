# Gemini Business API 服务
import re
import json
import httpx
from typing import List, Dict, Any, Optional
from app.logger import get_logger

logger = get_logger(__name__)


class GeminiAPIError(Exception):
    """Gemini API 错误"""
    def __init__(self, message: str, status_code: int = 0):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class GeminiAPI:
    """Gemini Business API 客户端
    
    使用 Google 的 batchexecute RPC 接口
    """
    
    BASE_URL = "https://business.gemini.google"
    RPC_PATH = "/settings/_/AgentspaceSaasSettingsUi/data/batchexecute"
    
    # RPC IDs
    RPC_GET_MEMBERS = "vlyShc"
    RPC_INVITE_MEMBER = "d0J11e"
    RPC_REMOVE_MEMBER = "wVjvl"
    
    def __init__(self, account_id: str, cookies: str):
        """
        初始化 Gemini API 客户端
        
        Args:
            account_id: Gemini Business 账户 ID (如 393661537155)
            cookies: 完整的 cookie 字符串
        """
        self.account_id = account_id
        self.cookies = cookies
        self.at_token: Optional[str] = None
        self.session_params: Dict[str, str] = {}
        
    def _parse_cookies(self) -> Dict[str, str]:
        """解析 cookie 字符串为字典"""
        cookies = {}
        for item in self.cookies.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key.strip()] = value.strip()
        return cookies
    
    async def _fetch_at_token(self, client: httpx.AsyncClient) -> str:
        """从页面获取 at token (SNlM0e)"""
        headers = {
            "Cookie": self.cookies,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
        }
        
        resp = await client.get(
            f"{self.BASE_URL}/settings/team",
            headers=headers,
            follow_redirects=True
        )
        
        if resp.status_code != 200:
            raise GeminiAPIError(f"获取页面失败: {resp.status_code}", resp.status_code)
        
        # 从 WIZ_global_data 中提取 SNlM0e
        match = re.search(r'"SNlM0e":"([^"]+)"', resp.text)
        if not match:
            raise GeminiAPIError("无法获取 at token，可能 cookie 已过期")
        
        self.at_token = match.group(1)
        
        # 提取其他会话参数
        fsid_match = re.search(r'"FdrFJe":"([^"]+)"', resp.text)
        if fsid_match:
            self.session_params['f.sid'] = fsid_match.group(1)
        
        bl_match = re.search(r'"cfb2h":"([^"]+)"', resp.text)
        if bl_match:
            self.session_params['bl'] = bl_match.group(1)
            
        return self.at_token

    async def _make_rpc_request(
        self, 
        client: httpx.AsyncClient,
        rpc_id: str, 
        params: Any
    ) -> Any:
        """发送 batchexecute RPC 请求"""
        if not self.at_token:
            await self._fetch_at_token(client)
        
        # 构建请求参数
        params_json = json.dumps(params)
        f_req = json.dumps([[[rpc_id, params_json, None, "generic"]]])
        
        query_params = {
            "rpcids": rpc_id,
            "source-path": "/settings/team",
            "bl": self.session_params.get('bl', 'boq_cloud-ml-agentspace-saasfe_20251119.08_p2'),
            "hl": "zh-CN",
            "rt": "c",
        }
        
        if 'f.sid' in self.session_params:
            query_params['f.sid'] = self.session_params['f.sid']
        
        headers = {
            "Cookie": self.cookies,
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
            "Origin": self.BASE_URL,
            "Referer": f"{self.BASE_URL}/",
            "X-Same-Domain": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
        }
        
        data = {
            "f.req": f_req,
            "at": self.at_token,
        }
        
        logger.info(f"Gemini RPC: {rpc_id}", extra={"account_id": self.account_id})
        
        resp = await client.post(
            f"{self.BASE_URL}{self.RPC_PATH}",
            params=query_params,
            headers=headers,
            data=data,
        )
        
        if resp.status_code != 200:
            raise GeminiAPIError(f"RPC 请求失败: {resp.status_code}", resp.status_code)
        
        # 解析响应
        return self._parse_response(resp.text, rpc_id)
    
    def _parse_response(self, text: str, rpc_id: str) -> Any:
        """解析 batchexecute 响应"""
        # 响应格式: )]}'\n数字\n[[...]]
        lines = text.split('\n')
        
        for line in lines:
            if line.startswith('[['):
                try:
                    data = json.loads(line)
                    # 查找对应的 RPC 响应
                    for item in data:
                        if isinstance(item, list) and len(item) > 2:
                            if item[0] == "wrb.fr" and item[1] == rpc_id:
                                # item[2] 是 JSON 字符串
                                if item[2]:
                                    return json.loads(item[2])
                                return None
                except json.JSONDecodeError:
                    continue
        
        return None

    async def get_members(self) -> List[Dict[str, Any]]:
        """获取团队成员列表
        
        Returns:
            成员列表，每个成员包含 email, role, member_id 等
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            result = await self._make_rpc_request(
                client,
                self.RPC_GET_MEMBERS,
                [self.account_id]
            )
        
        members = []
        if result and isinstance(result, list):
            for item in result:
                if isinstance(item, list):
                    for member_data in item:
                        if isinstance(member_data, list) and len(member_data) >= 4:
                            member = {
                                "email": member_data[2] if len(member_data) > 2 else None,
                                "role": member_data[3] if len(member_data) > 3 else "viewer",
                                "member_id": member_data[4] if len(member_data) > 4 else None,
                            }
                            if member["email"]:
                                members.append(member)
        
        logger.info(f"Gemini get_members: {len(members)} members", extra={"account_id": self.account_id})
        return members


    async def invite_member(self, email: str, role: str = "viewer") -> Dict[str, Any]:
        """邀请成员加入团队
        
        Args:
            email: 成员邮箱
            role: 角色，viewer 或 admin
            
        Returns:
            邀请结果
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            result = await self._make_rpc_request(
                client,
                self.RPC_INVITE_MEMBER,
                [self.account_id, [[None, None, email.lower().strip(), role]]]
            )
        
        logger.info(f"Gemini invite_member: {email}", extra={
            "account_id": self.account_id,
            "role": role
        })
        
        # 检查响应中是否有错误
        if result and isinstance(result, list):
            # 成功响应格式: [[[null,null,"email","role"]], null, [["email", 1, [...]]]]
            if len(result) >= 3 and result[2]:
                for item in result[2]:
                    if isinstance(item, list) and len(item) >= 2:
                        if item[1] == 1:  # 1 表示成功
                            return {"success": True, "email": email}
                        else:
                            return {"success": False, "email": email, "error": "邀请失败"}
        
        return {"success": True, "email": email}

    async def invite_members(self, emails: List[str], role: str = "viewer") -> Dict[str, Any]:
        """批量邀请成员
        
        Args:
            emails: 邮箱列表
            role: 角色
            
        Returns:
            邀请结果统计
        """
        results = {"success": [], "failed": []}
        
        for email in emails:
            try:
                result = await self.invite_member(email, role)
                if result.get("success"):
                    results["success"].append(email)
                else:
                    results["failed"].append({"email": email, "error": result.get("error", "未知错误")})
            except GeminiAPIError as e:
                results["failed"].append({"email": email, "error": e.message})
            except Exception as e:
                results["failed"].append({"email": email, "error": str(e)})
        
        return results

    async def remove_member(self, email: str) -> Dict[str, Any]:
        """移除团队成员
        
        Args:
            email: 成员邮箱
            
        Returns:
            移除结果
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            result = await self._make_rpc_request(
                client,
                self.RPC_REMOVE_MEMBER,
                [self.account_id, [email.lower().strip()]]
            )
        
        logger.info(f"Gemini remove_member: {email}", extra={"account_id": self.account_id})
        
        return {"success": True, "email": email}

    async def test_connection(self) -> Dict[str, Any]:
        """测试连接是否正常
        
        Returns:
            连接状态和成员数量
        """
        try:
            members = await self.get_members()
            return {
                "success": True,
                "member_count": len(members),
                "account_id": self.account_id
            }
        except GeminiAPIError as e:
            return {
                "success": False,
                "error": e.message,
                "account_id": self.account_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "account_id": self.account_id
            }
