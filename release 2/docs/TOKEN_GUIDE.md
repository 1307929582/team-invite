# ChatGPT Team Token 获取指南

## 只需要 3 个值

| 字段 | 说明 | 有效期 |
|------|------|--------|
| Account ID | Team 账户标识 (UUID) | 永久 |
| Session Token | JWT 认证令牌 | ~10 天 |
| Device ID | 设备标识 | 永久 |

---

## 获取方法

1. 登录 ChatGPT Team 管理后台
2. F12 打开开发者工具 → Network
3. 筛选 `backend-api`
4. 点击任意请求，查看 Request Headers

### Account ID
从 URL 中获取：
```
https://chatgpt.com/backend-api/accounts/eabecad0-0c6a-4932-aeb4-4ad932280677/users
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                        这就是 Account ID
```

### Session Token
从 Headers 中找：
```
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
                      ^^^^^^^^^^^^^^^^^^^^^^^
                      复制 Bearer 后面的内容
```

### Device ID
从 Headers 中找：
```
oai-device-id: 0f404cce-2645-42e0-8163-80947354fad3
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
               复制这个值
```

---

## Token 过期后

Session Token 约 10 天过期，届时需要：
1. 重新登录 ChatGPT
2. 抓取新的 Token
3. 在管理平台编辑 Team，更新 Token

Account ID 和 Device ID 不会变，不用重新填。

---

## 不需要 Cookie

经测试，只需要上述 3 个值即可正常调用 API，不需要完整的 Cookie。
