"""Add Kali permissions tables

Revision ID: be4990556a89
Revises: 337bdadb5a14
Create Date: 2026-09-12 15:42:06.751105

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be4990556a89'
down_revision: Union[str, Sequence[str], None] = '337bdadb5a14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # kali_permission_policies
    op.create_table(
        'kali_permission_policies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('allowed_permissions', sa.JSON(), nullable=True),
        sa.Column('denied_permissions', sa.JSON(), nullable=True),
        sa.Column('allowed_tools', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kali_permission_policies_project_id'), 'kali_permission_policies', ['project_id'], unique=False)
    op.create_index(op.f('ix_kali_permission_policies_user_id'), 'kali_permission_policies', ['user_id'], unique=False)

    # kali_approval_requests
    op.create_table(
        'kali_approval_requests',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('task_id', sa.String(), nullable=False),
        sa.Column('tool_name', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('resource', sa.String(), nullable=True),
        sa.Column('risk_level', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('requested_input_summary', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('rejection_reason', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kali_approval_requests_project_id'), 'kali_approval_requests', ['project_id'], unique=False)
    op.create_index(op.f('ix_kali_approval_requests_status'), 'kali_approval_requests', ['status'], unique=False)
    op.create_index(op.f('ix_kali_approval_requests_task_id'), 'kali_approval_requests', ['task_id'], unique=False)
    op.create_index(op.f('ix_kali_approval_requests_user_id'), 'kali_approval_requests', ['user_id'], unique=False)

    # kali_permission_decisions
    op.create_table(
        'kali_permission_decisions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('task_id', sa.String(), nullable=False),
        sa.Column('tool_name', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('risk_level', sa.String(), nullable=False),
        sa.Column('decision', sa.String(), nullable=False),
        sa.Column('allowed', sa.Boolean(), nullable=False),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('approval_id', sa.String(), nullable=True),
        sa.Column('policy_id', sa.String(), nullable=True),
        sa.Column('scope', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kali_permission_decisions_project_id'), 'kali_permission_decisions', ['project_id'], unique=False)
    op.create_index(op.f('ix_kali_permission_decisions_task_id'), 'kali_permission_decisions', ['task_id'], unique=False)
    op.create_index(op.f('ix_kali_permission_decisions_user_id'), 'kali_permission_decisions', ['user_id'], unique=False)


def downgrade() -> None:
    # kali_permission_decisions
    op.drop_index(op.f('ix_kali_permission_decisions_user_id'), table_name='kali_permission_decisions')
    op.drop_index(op.f('ix_kali_permission_decisions_task_id'), table_name='kali_permission_decisions')
    op.drop_index(op.f('ix_kali_permission_decisions_project_id'), table_name='kali_permission_decisions')
    op.drop_table('kali_permission_decisions')

    # kali_approval_requests
    op.drop_index(op.f('ix_kali_approval_requests_user_id'), table_name='kali_approval_requests')
    op.drop_index(op.f('ix_kali_approval_requests_task_id'), table_name='kali_approval_requests')
    op.drop_index(op.f('ix_kali_approval_requests_status'), table_name='kali_approval_requests')
    op.drop_index(op.f('ix_kali_approval_requests_project_id'), table_name='kali_approval_requests')
    op.drop_table('kali_approval_requests')

    # kali_permission_policies
    op.drop_index(op.f('ix_kali_permission_policies_user_id'), table_name='kali_permission_policies')
    op.drop_index(op.f('ix_kali_permission_policies_project_id'), table_name='kali_permission_policies')
    op.drop_table('kali_permission_policies')
