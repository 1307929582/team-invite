# Google Team 管理方案分析

## 1. Google 的 AI 订阅产品

### Google One AI Premium
- 价格：$19.99/月
- 包含：Gemini Advanced、2TB 存储、Google Workspace 中的 Gemini
- 个人订阅，不支持 Team 共享

### Google Workspace Business
- 价格：$12-$18/用户/月
- 包含：Gmail、Drive、Meet、Gemini for Workspace
- **支持组织管理，可以邀请成员**

---

## 2. Google Workspace 管理 API

Google 有官方的 Admin SDK，比 ChatGPT 友好很多：

### 2.1 Directory API（用户管理）
```
POST https://admin.googleapis.com/admin/directory/v1/users
- 创建用户
- 邀请用户
- 管理用户权限
```

### 2.2 Licensing API（许可证管理）
```
POST https://licensing.googleapis.com/apps/licensing/v1/product/{productId}/sku/{skuId}/user/{userId}
- 分配许可证
- 查看许可证使用情况
```

### 2.3 认证方式
- **OAuth 2.0** - 标准认证，需要用户授权
- **Service Account** - 服务账号，可以代表管理员操作（推荐）

---

## 3. 与 ChatGPT Team 的对比

| 特性 | ChatGPT Team | Google Workspace |
|------|-------------|------------------|
| 官方 API | ❌ 无，需要逆向 | ✅ 有完整 Admin SDK |
| 认证方式 | Session Token（10天过期） | OAuth/Service Account（长期有效） |
| 邀请成员 | 逆向 API，不稳定 | 官方 API，稳定 |
| 成员上限 | 软限制 5 人 | 按许可证数量 |
| 自动化难度 | 高 | 低 |

---

## 4. 集成方案

### 4.1 数据库改造
```python
class Team(Base):
    # 现有字段...
    
    # 新增：Team 类型
    team_type = Column(Enum("chatgpt", "google"), default="chatgpt")
    
    # Google 专用字段
    google_domain = Column(String(100))  # 组织域名
    google_customer_id = Column(String(100))  # 客户 ID
    google_credentials = Column(Text)  # Service Account JSON
```

### 4.2 API 服务抽象
```python
class TeamService(ABC):
    @abstractmethod
    async def get_members(self) -> List[Member]: pass
    
    @abstractmethod
    async def invite_member(self, email: str) -> bool: pass
    
    @abstractmethod
    async def remove_member(self, email: str) -> bool: pass

class ChatGPTTeamService(TeamService):
    # 现有实现...

class GoogleTeamService(TeamService):
    # Google Admin SDK 实现
```

### 4.3 前端改造
- 添加 Team 时选择类型（ChatGPT / Google）
- 根据类型显示不同的配置表单
- 统一的成员管理界面

---

## 5. Google Workspace 集成步骤

### 步骤 1：创建 Google Cloud 项目
1. 访问 https://console.cloud.google.com
2. 创建新项目
3. 启用 Admin SDK API

### 步骤 2：创建 Service Account
1. IAM & Admin → Service Accounts
2. 创建服务账号
3. 下载 JSON 密钥文件

### 步骤 3：授权域范围委派
1. Google Admin Console → Security → API Controls
2. 添加服务账号的 Client ID
3. 授权范围：
   - `https://www.googleapis.com/auth/admin.directory.user`
   - `https://www.googleapis.com/auth/apps.licensing`

### 步骤 4：代码实现
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user',
    'https://www.googleapis.com/auth/apps.licensing'
]

credentials = service_account.Credentials.from_service_account_file(
    'service-account.json',
    scopes=SCOPES,
    subject='admin@yourdomain.com'  # 管理员邮箱
)

# 用户管理
directory_service = build('admin', 'directory_v1', credentials=credentials)

# 列出用户
users = directory_service.users().list(domain='yourdomain.com').execute()

# 邀请用户
new_user = {
    'primaryEmail': 'newuser@yourdomain.com',
    'name': {'givenName': 'New', 'familyName': 'User'},
    'password': 'tempPassword123!'
}
directory_service.users().insert(body=new_user).execute()
```

---

## 6. 实现优先级

### Phase 1：基础集成
- [ ] 数据库增加 team_type 字段
- [ ] 创建 GoogleTeamService
- [ ] 前端添加 Team 类型选择

### Phase 2：功能完善
- [ ] Google 成员同步
- [ ] Google 邀请成员
- [ ] 许可证管理

### Phase 3：高级功能
- [ ] 统一的 Dashboard 展示
- [ ] 跨平台成员统计
- [ ] 自动化许可证分配

---

## 7. 注意事项

1. **Google Workspace 需要自定义域名**
   - 不能用 @gmail.com
   - 需要验证域名所有权

2. **Service Account 权限**
   - 需要超级管理员授权
   - 只能管理同一组织的用户

3. **费用**
   - Google Cloud API 有免费额度
   - 超出后按调用次数计费（很便宜）

4. **与 ChatGPT 的区别**
   - Google 是正规 API，不会被封
   - 但需要购买 Workspace 订阅

---

## 8. 下一步

确认是否要开始实现？需要你提供：
1. 是否已有 Google Workspace 订阅？
2. 是否有自定义域名？
3. 想先实现哪些功能？
