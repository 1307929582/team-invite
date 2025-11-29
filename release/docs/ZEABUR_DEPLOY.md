# Zeabur 部署指南

## 部署架构

```
Zeabur Project
├── PostgreSQL (数据库服务)
├── Backend (Python FastAPI)
└── Frontend (React 静态站点)
```

## 部署步骤

### 1. 创建项目

1. 登录 [Zeabur](https://zeabur.com)
2. 点击「Create Project」创建新项目
3. 选择区域（推荐选离你近的）

### 2. 添加 PostgreSQL 数据库

1. 在项目中点击「Add Service」
2. 选择「Marketplace」→「PostgreSQL」
3. 等待数据库启动完成
4. 点击数据库服务，复制连接信息：
   - `POSTGRES_URI`（完整连接字符串）

### 3. 部署后端

1. 点击「Add Service」→「Git」（或上传代码）
2. 选择 `backend` 目录
3. Zeabur 会自动识别为 Python 项目
4. 配置环境变量（点击服务 → Variables）：

```
DATABASE_URL = ${POSTGRES_URI}  # 绑定数据库
SECRET_KEY = 你的随机密钥（至少32位）
```

5. 等待构建完成
6. 绑定域名或使用 Zeabur 提供的域名

### 4. 部署前端

1. 点击「Add Service」→「Git」
2. 选择 `frontend` 目录
3. 配置环境变量：

```
VITE_API_URL = https://你的后端域名
```

4. 等待构建完成
5. 绑定域名

### 5. 配置前端 API 地址

部署前需要修改前端代码，让它指向后端域名。

编辑 `frontend/src/api/index.ts`：

```typescript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000,
})
```

编辑 `frontend/vite.config.ts`：

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3456,
    proxy: {
      '/api': {
        target: 'http://localhost:4567',
        changeOrigin: true
      }
    }
  },
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || '/api/v1')
  }
})
```

## 环境变量说明

### 后端必需变量

| 变量 | 说明 | 示例 |
|------|------|------|
| DATABASE_URL | PostgreSQL 连接串 | postgresql://user:pass@host:5432/db |
| SECRET_KEY | JWT 密钥 | 随机32位以上字符串 |

### 后端可选变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| DEBUG | 调试模式 | false |
| CORS_ORIGINS | 允许的前端域名 | ["*"] |

### 前端变量

| 变量 | 说明 |
|------|------|
| VITE_API_URL | 后端 API 地址 |

## 生成 SECRET_KEY

```bash
openssl rand -hex 32
```

或在线生成：https://generate-secret.vercel.app/32

## 初始化系统

部署完成后：

1. 访问前端域名
2. 系统会自动跳转到初始化页面
3. 设置管理员账号密码
4. 登录管理后台配置 LinuxDO OAuth 和 Team

## 常见问题

### 后端启动失败

检查 `DATABASE_URL` 是否正确绑定了 PostgreSQL 服务。

### 前端无法连接后端

1. 检查 `VITE_API_URL` 是否正确
2. 检查后端 CORS 配置是否允许前端域名

### 数据库连接超时

确保后端和数据库在同一个 Zeabur 项目中，使用内网连接。

## 费用估算

Zeabur 按使用量计费：
- PostgreSQL: ~$5/月起
- Backend: ~$3-5/月（取决于流量）
- Frontend: 静态站点免费或很便宜

小规模使用大约 $10/月左右。
