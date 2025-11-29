"""添加 Team 分组功能

Revision ID: 002_add_team_groups
Revises: 001_initial
Create Date: 2025-11-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002_add_team_groups'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建 team_groups 表
    op.create_table('team_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_team_groups_id'), 'team_groups', ['id'], unique=False)
    op.create_index(op.f('ix_team_groups_name'), 'team_groups', ['name'], unique=True)
    
    # 给 teams 表添加 group_id 字段
    op.add_column('teams', sa.Column('group_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_teams_group_id', 'teams', 'team_groups', ['group_id'], ['id'])
    
    # 给 redeem_codes 表添加 group_id 字段
    op.add_column('redeem_codes', sa.Column('group_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_redeem_codes_group_id', 'redeem_codes', 'team_groups', ['group_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_redeem_codes_group_id', 'redeem_codes', type_='foreignkey')
    op.drop_column('redeem_codes', 'group_id')
    
    op.drop_constraint('fk_teams_group_id', 'teams', type_='foreignkey')
    op.drop_column('teams', 'group_id')
    
    op.drop_index(op.f('ix_team_groups_name'), table_name='team_groups')
    op.drop_index(op.f('ix_team_groups_id'), table_name='team_groups')
    op.drop_table('team_groups')
