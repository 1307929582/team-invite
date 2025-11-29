# ChatGPT Team Manager

企业级 ChatGPT Team 自助上车管理平台

## 功能特性

### 用户端
- 兑换码上车 - 用户使用兑换码自助加入 Team
- LinuxDO 登录 - 集成 LinuxDO OAuth 认证
- 直接邀请链接 - 无需登录，直接使用兑换码
- 座位统计 - 实时显示可用座位数
- 自动分配 - 智能分配到未满的 Team

### 管理端
- 多 Team 管理 - 集中管理多个 ChatGPT Team
- 兑换码系统 - 批量生成、管理兑换码
- 批量邀请 - 一键邀请多个用户
- 成员同步 - 自动同步 Team 成员列表
- 数据统计 - Dashboard 展示关键指标
- 操作日志 - 完整的审计日志

## 技术栈

| 后端 | 前端 | 数据库 |
|------|------|--------|
| FastAPI | React 18 | SQLite (默认) |
| SQLAlchemy | TypeScript | PostgreSQL (可选) |
| JWT + bcrypt | Ant Design | |
| httpx | Zustand + Axios | |

## 快速部署

### Docker 部署（推荐）

**SQLite 版本（简单）：**
```bash
docker-compose up -d --build
```

**PostgreSQL 版本（生产推荐）：**
```bash
# 创建环境变量
cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_USER=teamadmin
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=team_manager
EOF

# 启动服务
docker-compose -f docker-compose.postgres.yml up -d --build
```

### 访问系统

| 服务 | 地址 |
|------|------|
| 用户端 | http://localhost:3456 |
| 管理后台 | http://localhost:3456/admin |
| API 文档 | http://localhost:4567/docs |

### 本地开发

```bash
# 后端
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 4567

# 前端（新终端）
cd frontend
npm install
npm run dev
```

## 使用指南

1. **首次部署** - 访问系统会自动跳转到初始化页面，设置管理员账号
2. **配置 OAuth** - 登录管理后台 → 系统设置 → 配置 LinuxDO OAuth
3. **添加 Team** - 进入「Team 管理」→ 添加 Team → 填写 Token 信息
4. **生成兑换码** - 进入「兑换码管理」→ 批量生成 → 分发给用户

## 项目结构

```
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── routers/      # API 路由
│   │   ├── services/     # 业务逻辑
│   │   ├── models.py     # 数据模型
│   │   └── database.py   # 数据库配置
│   └── Dockerfile
├── frontend/             # React + TypeScript
│   ├── src/
│   │   ├── pages/        # 页面组件
│   │   ├── components/   # 通用组件
│   │   ├── api/          # API 封装
│   │   └── store/        # 状态管理
│   └── Dockerfile
└── docs/                 # 文档
```

## 安全特性

- JWT Token 认证
- 密码 bcrypt 加密
- 首次部署强制初始化
- 兑换码防暴力破解
- 前端路由守卫
- 敏感数据不暴露

## 注意事项

- Session Token 有效期约 7-30 天，过期需更新
- 批量邀请已内置 1 秒间隔，避免触发 Rate Limit
- 生产环境必须使用 HTTPS
- 定期备份数据库文件
