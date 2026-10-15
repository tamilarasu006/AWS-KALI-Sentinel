"""Add tool_executions

Revision ID: 337bdadb5a14
Revises: b2c3d4e5f6g7
Create Date: 2026-09-12 15:26:57.185839

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '337bdadb5a14'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'kali_tool_executions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('task_id', sa.String(), nullable=False),
        sa.Column('tool_name', sa.String(), nullable=False),
        sa.Column('tool_version', sa.String(), nullable=True),
        sa.Column('risk_level', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('input_metadata', sa.JSON(), nullable=True),
        sa.Column('output_metadata', sa.JSON(), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kali_tool_executions_user_id'), 'kali_tool_executions', ['user_id'], unique=False)
    op.create_index(op.f('ix_kali_tool_executions_project_id'), 'kali_tool_executions', ['project_id'], unique=False)
    op.create_index(op.f('ix_kali_tool_executions_task_id'), 'kali_tool_executions', ['task_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_kali_tool_executions_task_id'), table_name='kali_tool_executions')
    op.drop_index(op.f('ix_kali_tool_executions_project_id'), table_name='kali_tool_executions')
    op.drop_index(op.f('ix_kali_tool_executions_user_id'), table_name='kali_tool_executions')
    op.drop_table('kali_tool_executions')
