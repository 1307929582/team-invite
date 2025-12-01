"""add is_unauthorized to team_members

Revision ID: 005_add_unauthorized
Revises: 004_add_group_alert
Create Date: 2024-12-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_unauthorized'
down_revision = '004_add_group_alert'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 is_unauthorized 字段到 team_members 表
    op.add_column('team_members', sa.Column('is_unauthorized', sa.Boolean(), nullable=True, server_default='false'))


def downgrade():
    op.drop_column('team_members', 'is_unauthorized')
