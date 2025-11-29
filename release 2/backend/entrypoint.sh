#!/bin/sh
set -e

# 等待数据库就绪
echo "Waiting for database..."
sleep 2

# 修复迁移版本记录
echo "Fixing migration version records..."
python -c "
import os
from sqlalchemy import create_engine, text

database_url = os.environ.get('DATABASE_URL', 'sqlite:///./data/team_manager.db')
engine = create_engine(database_url)

try:
    with engine.connect() as conn:
        # 检查 alembic_version 表是否存在
        result = conn.execute(text(\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')\"))
        table_exists = result.scalar()
        
        if not table_exists:
            print('alembic_version table does not exist, will be created by alembic')
        else:
            # 检查当前版本
            result = conn.execute(text('SELECT version_num FROM alembic_version'))
            rows = result.fetchall()
            
            # 检查数据表是否已存在（判断数据库是否已初始化）
            result = conn.execute(text(\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'teams')\"))
            teams_exists = result.scalar()
            
            if rows:
                current_version = rows[0][0]
                print(f'Current migration version: {current_version}')
                
                # 如果是旧的 gemini 版本，更新到新版本
                if 'gemini' in current_version.lower():
                    conn.execute(text(\"UPDATE alembic_version SET version_num = '003_remove_gemini'\"))
                    conn.commit()
                    print('Updated migration version to 003_remove_gemini')
            elif teams_exists:
                # 没有版本记录但表已存在，说明版本记录被清空了
                # 直接设置到最新版本
                print('No version record but tables exist, setting to latest version')
                conn.execute(text(\"INSERT INTO alembic_version (version_num) VALUES ('003_remove_gemini')\"))
                conn.commit()
                print('Inserted migration version 003_remove_gemini')
            else:
                print('Fresh database, will run all migrations')
except Exception as e:
    print(f'Migration fix error: {e}')
"

# 运行数据库迁移
echo "Running database migrations..."
alembic upgrade head

# 启动应用
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 4567 --workers 4
