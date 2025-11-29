"""Remove Gemini tables

Revision ID: 003_remove_gemini
Revises: 002_add_team_groups
Create Date: 2025-11-27

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_remove_gemini'
down_revision = '002_add_team_groups'
branch_labels = None
depends_on = None


def upgrade():
    # 删除 Gemini 相关表（如果存在）
    op.execute("DROP TABLE IF EXISTS gemini_invite_records CASCADE")
    op.execute("DROP TABLE IF EXISTS gemini_members CASCADE")
    op.execute("DROP TABLE IF EXISTS gemini_teams CASCADE")
    
    # 清理旧的迁移记录（处理从 003_add_gemini 升级的情况）
    op.execute("DELETE FROM alembic_version WHERE version_num = '003_add_gemini'")


def downgrade():
    # 不需要恢复 Gemini 表
    pass
