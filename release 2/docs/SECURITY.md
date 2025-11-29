# 安全说明

## 已实施的安全措施

### 1. 认证与授权
- ✅ JWT Token 认证，7天有效期
- ✅ 所有管理员接口都需要 `get_current_user` 或 `get_current_admin` 验证
- ✅ 密码使用 bcrypt 加密存储
- ✅ 首次部署必须通过 `/setup/initialize` 设置管理员账号
- ✅ 初始化后无法重复设置，防止覆盖攻击

### 2. 接口权限分级

#### 公开接口（无需认证）
- `GET /api/v1/setup/status` - 查看系统初始化状态
- `POST /api/v1/setup/initialize` - 初始化系统（仅未初始化时可用）
- `GET /api/v1/public/linuxdo/auth` - 获取 LinuxDO OAuth URL
- `POST /api/v1/public/linuxdo/callback` - LinuxDO OAuth 回调
- `GET /api/v1/public/user/status` - 查询用户状态
- `POST /api/v1/public/redeem` - 使用兑换码
- `GET /api/v1/public/seats` - 查看座位统计

#### 管理员接口（需要 JWT Token）
- `/api/v1/auth/*` - 认证管理
- `/api/v1/teams/*` - Team 管理
- `/api/v1/dashboard/*` - 数据统计
- `/api/v1/redeem-codes/*` - 兑换码管理
- `/api/v1/config/*` - 系统配置
- `/api/v1/linuxdo-users/*` - 用户管理

### 3. 数据安全
- ✅ 敏感字段（session_token, cookie）不在 API 响应中暴露
- ✅ 密码字段使用 bcrypt 单向加密
- ✅ JWT Secret Key 在初始化时自动生成随机值
- ✅ 数据库文件 `backend/data/` 已加入 .gitignore

### 4. 输入验证
- ✅ 邮箱格式验证
- ✅ 密码长度验证（最少6位）
- ✅ 用户名长度验证（最少3位）
- ✅ Token 自动清理首尾空格

### 5. 防护措施
- ✅ CORS 配置（生产环境需要限制域名）
- ✅ 401 自动跳转登录页
- ✅ 前端路由守卫，未登录无法访问管理后台
- ✅ 初始化检查，未初始化强制跳转设置页

## 需要注意的安全配置

### 1. 生产环境部署前

#### 修改 CORS 配置
编辑 `backend/app/main.py`：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 改为你的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 修改 JWT Secret Key
初始化时会自动生成，但建议在 `backend/app/config.py` 中设置更强的默认值：
```python
SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
```

#### 使用 HTTPS
生产环境必须使用 HTTPS，防止 Token 被中间人攻击窃取。

### 2. 环境变量配置

创建 `backend/.env` 文件：
```env
# 数据库（可选，默认使用 SQLite）
DATABASE_URL=sqlite:///./data/app.db

# JWT 配置（可选，会自动生成）
SECRET_KEY=your-random-secret-key-here

# CORS 配置
CORS_ORIGINS=["https://your-domain.com"]
```

### 3. 防火墙配置

如果使用云服务器，建议：
- 只开放 80 (HTTP) 和 443 (HTTPS) 端口
- 后端 API 端口 (8000) 不对外暴露，通过 Nginx 反向代理
- 数据库端口不对外开放

### 4. Nginx 反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. 定期备份

定期备份数据库文件：
```bash
# 备份数据库
cp backend/data/app.db backend/data/app.db.backup.$(date +%Y%m%d)

# 保留最近7天的备份
find backend/data/ -name "app.db.backup.*" -mtime +7 -delete
```

## 已知风险点

### 1. LinuxDO OAuth Token
- LinuxDO 用户的 token 存储在前端 localStorage
- 建议：定期清理，或改为后端 Session 管理

### 2. 兑换码暴力破解
- 当前兑换码为 8 位大写字母+数字
- 建议：添加速率限制，限制每个 IP 每分钟最多尝试 5 次

### 3. Session Token 泄露
- ChatGPT Session Token 存储在数据库中
- 建议：定期检查 Token 有效期，及时更新

## 安全检查清单

部署前请确认：

- [ ] 已修改 CORS 配置为生产域名
- [ ] 已配置 HTTPS 证书
- [ ] 已设置强密码的管理员账号
- [ ] 已配置防火墙规则
- [ ] 已设置 Nginx 反向代理
- [ ] 已配置定期数据库备份
- [ ] 已检查 .gitignore 不会上传敏感文件
- [ ] 已删除测试用的管理员账号
- [ ] 已配置 LinuxDO OAuth 回调地址

## 应急响应

### 如果管理员密码泄露

1. 立即登录管理后台修改密码
2. 检查操作日志，确认是否有异常操作
3. 如果无法登录，删除数据库重新初始化

### 如果 Session Token 泄露

1. 立即在 ChatGPT 官网登出所有设备
2. 重新获取 Session Token
3. 在管理后台更新 Team 配置

### 如果数据库泄露

1. 立即修改所有管理员密码
2. 重新生成所有兑换码
3. 通知所有用户可能的数据泄露风险
