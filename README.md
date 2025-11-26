<div align="center">

# 🚀 ChatGPT Team Manager

<p>
  <strong>企业级 ChatGPT Team 自助上车管理平台</strong>
</p>

<p>
  <a href="#-功能特性">功能特性</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-使用指南">使用指南</a> •
  <a href="#-部署文档">部署文档</a> •
  <a href="#-技术栈">技术栈</a>
</p>

<p>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/Ant%20Design-0170FE?style=flat-square&logo=antdesign&logoColor=white" alt="Ant Design">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker">
</p>

<p>
  <img src="https://img.shields.io/github/license/1307929582/team-invite?style=flat-square" alt="License">
  <img src="https://img.shields.io/github/stars/1307929582/team-invite?style=flat-square" alt="Stars">
</p>

</div>

---

## ✨ 功能特性

<table>
<tr>
<td width="50%">

### 👤 用户端
- 🎫 **兑换码上车** - 用户使用兑换码自助加入 Team
- 🔐 **LinuxDO 登录** - 集成 LinuxDO OAuth 认证
- 🔗 **直接邀请链接** - 无需登录，直接使用兑换码
- 📊 **座位统计** - 实时显示可用座位数
- 🎯 **自动分配** - 智能分配到未满的 Team

</td>
<td width="50%">

### 🛠️ 管理端
- 👥 **多 Team 管理** - 集中管理多个 ChatGPT Team
- 🎟️ **兑换码系统** - 批量生成、管理兑换码
- 📧 **批量邀请** - 一键邀请多个用户
- 🔄 **成员同步** - 自动同步 Team 成员列表
- 📈 **数据统计** - Dashboard 展示关键指标
- 📝 **操作日志** - 完整的审计日志

</td>
</tr>
</table>

## 🚀 快速开始

### 一键部署（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/1307929582/team-invite/main/install.sh | bash
```

脚本会引导你选择数据库类型（SQLite/PostgreSQL）并自动完成部署。

### 手动 Docker 部署

<details>
<summary>SQLite 版本（简单）</summary>

```bash
git clone https://github.com/1307929582/team-invite.git
cd team-invite
docker-compose up -d --build
```

</details>

<details>
<summary>PostgreSQL 版本（生产推荐）</summary>

```bash
git clone https://github.com/1307929582/team-invite.git
cd team-invite

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

</details>

### 访问系统

| 服务 | 地址 |
|------|------|
| 用户端 | http://localhost:3456 |
| 管理后台 | http://localhost:3456/admin |
| API 文档 | http://localhost:4567/docs |

### 本地开发

<details>
<summary>点击展开</summary>

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

</details>

## 📖 使用指南

### 1️⃣ 首次部署 - 系统初始化

首次访问会自动跳转到初始化页面，设置管理员账号。

> ⚠️ **重要**：初始化后无法重复设置，请牢记管理员账号密码！

### 2️⃣ 配置 LinuxDO OAuth

登录管理后台 → 系统设置 → 配置 OAuth 信息

### 3️⃣ 添加 Team

进入「Team 管理」→ 添加 Team → 填写 Token 信息

📖 参考 [Token 获取指南](docs/TOKEN_GUIDE.md)

### 4️⃣ 生成兑换码

进入「兑换码管理」→ 批量生成 → 分发给用户

### 5️⃣ 用户使用流程

```
访问首页 → LinuxDO 登录 → 输入邮箱和兑换码 → 自动分配 Team → 查收邮件接受邀请
```

## 🏗️ 项目结构

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
├── docs/                 # 文档
└── docker-compose.yml
```

## 🔧 技术栈

| 后端 | 前端 | 数据库 |
|------|------|--------|
| FastAPI | React 18 | SQLite (默认) |
| SQLAlchemy | TypeScript | PostgreSQL (可选) |
| JWT + bcrypt | Ant Design | |
| httpx | Zustand + Axios | |

## 🔒 安全特性

- ✅ JWT Token 认证
- ✅ 密码 bcrypt 加密
- ✅ 首次部署强制初始化
- ✅ 兑换码防暴力破解
- ✅ 前端路由守卫
- ✅ 敏感数据不暴露

详见 [安全说明](docs/SECURITY.md)

## 📦 部署文档

详见 [部署指南](docs/DEPLOYMENT.md)

<details>
<summary>快速部署清单</summary>

- [ ] 配置域名和 SSL 证书
- [ ] 修改 CORS 配置为生产域名
- [ ] 配置 Nginx 反向代理
- [ ] 设置防火墙规则
- [ ] 配置定期数据库备份
- [ ] 初始化管理员账号
- [ ] 配置 LinuxDO OAuth

</details>

## ⚠️ 注意事项

- Session Token 有效期约 7-30 天，过期需更新
- 批量邀请已内置 1 秒间隔，避免触发 Rate Limit
- 生产环境必须使用 HTTPS
- 定期备份数据库文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

[MIT License](LICENSE)

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [Ant Design](https://ant.design/)
- [LinuxDO](https://linux.do/)

---

<div align="center">
  <sub>Made with ❤️ for ChatGPT Team managers</sub>
</div>
