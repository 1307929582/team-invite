#!/bin/sh
set -e

# 等待数据库就绪
echo "Waiting for database..."
sleep 2

# 清理无效的迁移记录（处理删除的迁移文件）
echo "Cleaning up invalid migration records..."
python -c "
import os
from sqlalchemy import create_engine, text

database_url = os.environ.get('DATABASE_URL', 'sqlite:///./data/team_manager.db')
engine = create_engine(database_url)

try:
    with engine.connect() as conn:
        # 删除不存在的迁移版本记录
        result = conn.execute(text(\"DELETE FROM alembic_version WHERE version_num LIKE '%gemini%'\"))
        conn.commit()
        print(f'Cleaned up {result.rowcount} invalid migration records')
except Exception as e:
    print(f'Migration cleanup skipped: {e}')
"

# 运行数据库迁移
echo "Running database migrations..."
alembic upgrade head

# 启动应用
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 4567 --workers 4
