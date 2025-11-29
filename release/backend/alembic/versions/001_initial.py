"""初始数据库结构

Revision ID: 001_initial
Revises: 
Create Date: 2025-11-26

这是初始迁移，标记现有数据库结构。
如果是全新部署，会创建所有表。
如果是已有数据库，只需标记版本。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 检查表是否已存在，如果存在则跳过
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'users' not in existing_tables:
        op.create_table('users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(50), nullable=False),
            sa.Column('email', sa.String(100), nullable=False),
            sa.Column('hashed_password', sa.String(255), nullable=False),
            sa.Column('role', sa.Enum('ADMIN', 'OPERATOR', 'VIEWER', name='userrole'), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
        op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
        op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    if 'teams' not in existing_tables:
        op.create_table('teams',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('account_id', sa.String(100), nullable=False),
            sa.Column('session_token', sa.Text(), nullable=False),
            sa.Column('device_id', sa.String(100), nullable=True),
            sa.Column('cookie', sa.Text(), nullable=True),
            sa.Column('token_expires_at', sa.DateTime(), nullable=True),
            sa.Column('max_seats', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_teams_id'), 'teams', ['id'], unique=False)
    
    if 'linuxdo_users' not in existing_tables:
        op.create_table('linuxdo_users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('linuxdo_id', sa.String(100), nullable=False),
            sa.Column('username', sa.String(100), nullable=False),
            sa.Column('name', sa.String(100), nullable=True),
            sa.Column('email', sa.String(100), nullable=True),
            sa.Column('trust_level', sa.Integer(), nullable=True),
            sa.Column('avatar_url', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('last_login', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_linuxdo_users_id'), 'linuxdo_users', ['id'], unique=False)
        op.create_index(op.f('ix_linuxdo_users_linuxdo_id'), 'linuxdo_users', ['linuxdo_id'], unique=True)
    
    if 'redeem_codes' not in existing_tables:
        op.create_table('redeem_codes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('code', sa.String(50), nullable=False),
            sa.Column('code_type', sa.Enum('LINUXDO', 'DIRECT', name='redeemcodetype'), nullable=True),
            sa.Column('max_uses', sa.Integer(), nullable=True),
            sa.Column('used_count', sa.Integer(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('note', sa.String(255), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_redeem_codes_code'), 'redeem_codes', ['code'], unique=True)
        op.create_index(op.f('ix_redeem_codes_id'), 'redeem_codes', ['id'], unique=False)
    
    if 'system_configs' not in existing_tables:
        op.create_table('system_configs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('key', sa.String(100), nullable=False),
            sa.Column('value', sa.Text(), nullable=True),
            sa.Column('description', sa.String(255), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_system_configs_id'), 'system_configs', ['id'], unique=False)
        op.create_index(op.f('ix_system_configs_key'), 'system_configs', ['key'], unique=True)
    
    if 'team_members' not in existing_tables:
        op.create_table('team_members',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('team_id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(100), nullable=False),
            sa.Column('name', sa.String(100), nullable=True),
            sa.Column('role', sa.String(50), nullable=True),
            sa.Column('chatgpt_user_id', sa.String(100), nullable=True),
            sa.Column('joined_at', sa.DateTime(), nullable=True),
            sa.Column('synced_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_team_members_id'), 'team_members', ['id'], unique=False)
    
    if 'invite_records' not in existing_tables:
        op.create_table('invite_records',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('team_id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(100), nullable=False),
            sa.Column('linuxdo_user_id', sa.Integer(), nullable=True),
            sa.Column('status', sa.Enum('PENDING', 'SUCCESS', 'FAILED', name='invitestatus'), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('invited_by', sa.Integer(), nullable=True),
            sa.Column('redeem_code', sa.String(50), nullable=True),
            sa.Column('batch_id', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('accepted_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ),
            sa.ForeignKeyConstraint(['linuxdo_user_id'], ['linuxdo_users.id'], ),
            sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_invite_records_id'), 'invite_records', ['id'], unique=False)
    
    if 'operation_logs' not in existing_tables:
        op.create_table('operation_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('team_id', sa.Integer(), nullable=True),
            sa.Column('action', sa.String(50), nullable=False),
            sa.Column('target', sa.String(255), nullable=True),
            sa.Column('details', sa.Text(), nullable=True),
            sa.Column('ip_address', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_operation_logs_id'), 'operation_logs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('operation_logs')
    op.drop_table('invite_records')
    op.drop_table('team_members')
    op.drop_table('system_configs')
    op.drop_table('redeem_codes')
    op.drop_table('linuxdo_users')
    op.drop_table('teams')
    op.drop_table('users')
