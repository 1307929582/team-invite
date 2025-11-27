"""add gemini tables

Revision ID: 002_add_gemini
Revises: 001_initial
Create Date: 2025-11-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_gemini'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Gemini Teams 表
    op.create_table(
        'gemini_teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('account_id', sa.String(100), nullable=False),
        sa.Column('cookies', sa.Text(), nullable=False),
        sa.Column('max_seats', sa.Integer(), default=10),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gemini_teams_id'), 'gemini_teams', ['id'], unique=False)

    # Gemini Members 表
    op.create_table(
        'gemini_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('role', sa.String(50), default='viewer'),
        sa.Column('gemini_member_id', sa.Integer(), nullable=True),
        sa.Column('synced_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['gemini_teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gemini_members_id'), 'gemini_members', ['id'], unique=False)

    # Gemini Invite Records 表
    op.create_table(
        'gemini_invite_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('role', sa.String(50), default='viewer'),
        sa.Column('status', sa.Enum('pending', 'success', 'failed', name='invitestatus'), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('invited_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['gemini_teams.id'], ),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gemini_invite_records_id'), 'gemini_invite_records', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_gemini_invite_records_id'), table_name='gemini_invite_records')
    op.drop_table('gemini_invite_records')
    op.drop_index(op.f('ix_gemini_members_id'), table_name='gemini_members')
    op.drop_table('gemini_members')
    op.drop_index(op.f('ix_gemini_teams_id'), table_name='gemini_teams')
    op.drop_table('gemini_teams')
