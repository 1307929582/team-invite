"""add is_unauthorized to team_members

Revision ID: 005
Revises: 004
Create Date: 2024-12-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 is_unauthorized 字段到 team_members 表
    op.add_column('team_members', sa.Column('is_unauthorized', sa.Boolean(), nullable=True, default=False))
    
    # 设置默认值
    op.execute("UPDATE team_members SET is_unauthorized = false WHERE is_unauthorized IS NULL")


def downgrade():
    op.drop_column('team_members', 'is_unauthorized')
