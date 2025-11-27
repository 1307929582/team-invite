# Gemini Business 管理指南

本系统支持管理 Gemini Business 团队成员，功能包括：
- 添加/管理多个 Gemini Business 账户
- 查看团队成员列表
- 邀请新成员
- 移除成员
- 同步成员数据

## 获取凭证

### 1. 获取账户 ID (account_id)

1. 登录 [Gemini Business 管理后台](https://business.gemini.google/settings/team)
2. 查看浏览器地址栏 URL，找到 `project=` 参数
3. 例如：`https://business.gemini.google/settings/team?project=393661537155`
4. `393661537155` 就是你的账户 ID

### 2. 获取 Cookies

1. 登录 Gemini Business 管理后台
2. 按 F12 打开开发者工具
3. 切换到 **Application** (应用) 面板
4. 左侧选择 **Cookies** → `https://business.gemini.google`
5. 复制以下 Cookie 的值：
   - `__Host-C_OSES`
   - `__Secure-C_SES`
   - `NID`

6. 组合成完整的 Cookie 字符串：
```
__Host-C_OSES=xxx; __Secure-C_SES=xxx; NID=xxx
```

或者更简单的方法：
1. 在 Network 面板中找到任意请求
2. 复制请求头中的完整 `Cookie` 值

## 添加 Gemini Team

1. 进入管理后台 → **Gemini 管理**
2. 点击 **添加 Team**
3. 填写：
   - **名称**：自定义名称，如 "Gemini Team 1"
   - **账户 ID**：从 URL 获取的 project 参数
   - **Cookies**：完整的 Cookie 字符串
   - **最大座位数**：团队最大成员数
4. 点击创建，系统会自动测试连接并同步成员

## 邀请成员

1. 在 Team 列表中点击要管理的 Team
2. 点击 **邀请成员**
3. 输入邮箱列表（每行一个）
4. 选择角色：
   - `viewer`：普通成员
   - `admin`：管理员
5. 点击邀请

## 移除成员

1. 在成员列表中找到要移除的成员
2. 点击删除按钮
3. 确认移除

## Cookie 有效期

Gemini Business 的 Cookie 有效期通常为：
- `__Secure-C_SES`：约 1-2 周
- `NID`：约 6 个月

建议定期检查连接状态，如果失效需要重新获取 Cookie。

## 注意事项

1. **Cookie 安全**：Cookie 包含登录凭证，请妥善保管
2. **操作频率**：避免频繁操作，以免触发 Google 的安全限制
3. **成员上限**：注意不要超过订阅的座位数
4. **定期同步**：建议定期点击同步按钮更新成员数据

## API 接口

如果需要通过 API 操作，可以使用以下接口：

### 获取 Team 列表
```
GET /api/v1/gemini/teams
```

### 创建 Team
```
POST /api/v1/gemini/teams
{
  "name": "Gemini Team 1",
  "account_id": "393661537155",
  "cookies": "...",
  "max_seats": 10
}
```

### 邀请成员
```
POST /api/v1/gemini/teams/{team_id}/invite
{
  "emails": ["user@example.com"],
  "role": "viewer"
}
```

### 移除成员
```
POST /api/v1/gemini/teams/{team_id}/remove
{
  "email": "user@example.com"
}
```

### 同步成员
```
POST /api/v1/gemini/teams/{team_id}/sync
```

### 测试连接
```
POST /api/v1/gemini/teams/{team_id}/test
```
