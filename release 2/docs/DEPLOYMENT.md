# 部署指南

## 快速部署（Docker）

### 1. 准备工作

确保服务器已安装：
- Docker
- Docker Compose
- Git

### 2. 解压代码

```bash
# 将代码解压到目标目录
unzip chatgpt-team-manager.zip
cd chatgpt-team-manager
```

### 3. 配置环境变量（可选）

```bash
cp backend/.env.example backend/.env
# 编辑 .env 文件（可选，系统会自动生成配置）
nano backend/.env
```

### 4. 启动服务

```bash
docker-compose up -d --build
```

服务将在以下端口启动：
- 前端：http://localhost:3456
- 后端 API：http://localhost:4567

### 5. 初始化系统

首次访问会自动跳转到初始化页面：
1. 访问 http://your-domain.com
2. 设置管理员账号和密码
3. 完成初始化

### 6. 配置 LinuxDO OAuth

登录管理后台后：
1. 进入「系统设置」页面
2. 配置 LinuxDO OAuth 信息：
   - Client ID
   - Client Secret  
   - Redirect URI（如：https://your-domain.com/callback）

### 7. 添加 Team

1. 进入「Team 管理」
2. 点击「添加 Team」
3. 填写 Team 信息：
   - Team 名称
   - Account ID
   - Session Token
   - Device ID（可选）
   - 最大座位数

参考 [TOKEN_GUIDE.md](./TOKEN_GUIDE.md) 获取 Token。

### 8. 生成兑换码

1. 进入「兑换码管理」
2. 批量生成兑换码
3. 分发给用户使用

## 生产环境部署

### 使用 Nginx 反向代理

创建 `/etc/nginx/sites-available/chatgpt-team-manager`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书配置
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # 前端
    location / {
        proxy_pass http://localhost:3456;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://localhost:4567;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 日志
    access_log /var/log/nginx/chatgpt-team-manager.access.log;
    error_log /var/log/nginx/chatgpt-team-manager.error.log;
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/chatgpt-team-manager /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 配置 SSL 证书（Let's Encrypt）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 修改 CORS 配置

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

重新构建：
```bash
docker-compose down
docker-compose up -d --build
```

### 配置防火墙

```bash
# 只开放 HTTP 和 HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 设置自动备份

创建备份脚本 `/root/backup-chatgpt-team.sh`：

```bash
#!/bin/bash
BACKUP_DIR="/root/backups/chatgpt-team"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
cp /path/to/chatgpt-team-manager/backend/data/app.db \
   $BACKUP_DIR/app.db.$DATE

# 保留最近30天的备份
find $BACKUP_DIR -name "app.db.*" -mtime +30 -delete

echo "Backup completed: $DATE"
```

添加到 crontab：
```bash
chmod +x /root/backup-chatgpt-team.sh
crontab -e
# 每天凌晨2点备份
0 2 * * * /root/backup-chatgpt-team.sh >> /var/log/chatgpt-team-backup.log 2>&1
```

## 手动部署（不使用 Docker）

### 后端部署

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 4567
```

使用 systemd 管理服务，创建 `/etc/systemd/system/chatgpt-team-backend.service`：

```ini
[Unit]
Description=ChatGPT Team Manager Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/chatgpt-team-manager/backend
Environment="PATH=/path/to/chatgpt-team-manager/backend/venv/bin"
ExecStart=/path/to/chatgpt-team-manager/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 4567
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable chatgpt-team-backend
sudo systemctl start chatgpt-team-backend
```

### 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 使用 serve 或 nginx 托管 dist 目录
npm install -g serve
serve -s dist -l 3456
```

或使用 Nginx 直接托管：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/chatgpt-team-manager/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:4567;
    }
}
```

## 更新部署

```bash
cd chatgpt-team-manager

# 替换新版本代码后重新构建
docker-compose down
docker-compose up -d --build
```

## 监控和日志

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 查看所有日志
docker-compose logs

# 查看后端日志
docker-compose logs backend

# 查看前端日志
docker-compose logs frontend

# 实时查看日志
docker-compose logs -f
```

### 进入容器

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh
```

## 故障排查

### 后端无法启动

1. 检查端口是否被占用：`lsof -i:8000`
2. 检查数据库文件权限：`ls -la backend/data/`
3. 查看详细日志：`docker-compose logs backend`

### 前端无法访问

1. 检查端口是否被占用：`lsof -i:3000`
2. 检查 API 地址配置
3. 查看浏览器控制台错误

### Token 验证失败

1. 确认 Session Token 是否过期
2. 重新获取 Token 并更新
3. 检查 Device ID 是否正确

### 数据库损坏

1. 停止服务：`docker-compose down`
2. 恢复备份：`cp backup/app.db.xxx backend/data/app.db`
3. 重启服务：`docker-compose up -d`

## 性能优化

### 数据库优化

SQLite 默认配置已足够，如需更高性能可迁移到 PostgreSQL：

```python
# backend/app/config.py
DATABASE_URL: str = "postgresql://user:password@localhost/chatgpt_team"
```

### 缓存配置

可添加 Redis 缓存座位统计等高频查询数据。

### CDN 加速

将前端静态资源部署到 CDN，提升访问速度。

## 安全建议

详见 [SECURITY.md](./SECURITY.md)
