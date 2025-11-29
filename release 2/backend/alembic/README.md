# 数据库迁移指南

## 常用命令

### 查看当前版本
```bash
alembic current
```

### 查看迁移历史
```bash
alembic history
```

### 升级到最新版本
```bash
alembic upgrade head
```

### 回滚一个版本
```bash
alembic downgrade -1
```

### 创建新迁移
```bash
alembic revision --autogenerate -m "描述变更内容"
```

## Docker 环境使用

```bash
# 进入容器
docker compose -f docker-compose.postgres.yml exec backend bash

# 执行迁移
alembic upgrade head
```

## 首次部署（已有数据库）

如果数据库已有数据，需要标记当前版本：
```bash
alembic stamp head
```

## 添加新字段示例

1. 修改 `app/models.py` 添加新字段
2. 生成迁移文件：
   ```bash
   alembic revision --autogenerate -m "add xxx field"
   ```
3. 检查生成的迁移文件
4. 执行迁移：
   ```bash
   alembic upgrade head
   ```
