"""Add KALI Core Runtime models

Revision ID: a1b2c3d4e5f6
Revises: e61662d411e8
Create Date: 2026-09-12 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'e61662d411e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # kali_projects
    op.create_table('kali_projects',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('objective', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kali_projects_user_id'), 'kali_projects', ['user_id'], unique=False)

    # kali_tasks
    op.create_table('kali_tasks',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('parent_task_id', sa.String(), nullable=True),
    sa.Column('project_id', sa.String(), nullable=True),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('objective', sa.Text(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('dependencies', sa.JSON(), nullable=False),
    sa.Column('artifacts', sa.JSON(), nullable=False),
    sa.Column('assigned_agent', sa.String(), nullable=True),
    sa.Column('assigned_tool', sa.String(), nullable=True),
    sa.Column('input_data', sa.JSON(), nullable=True),
    sa.Column('output_data', sa.JSON(), nullable=True),
    sa.Column('errors', sa.JSON(), nullable=True),
    sa.Column('retry_count', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['parent_task_id'], ['kali_tasks.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['kali_projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kali_tasks_parent_task_id'), 'kali_tasks', ['parent_task_id'], unique=False)
    op.create_index(op.f('ix_kali_tasks_project_id'), 'kali_tasks', ['project_id'], unique=False)
    op.create_index(op.f('ix_kali_tasks_user_id'), 'kali_tasks', ['user_id'], unique=False)

    # kali_runtime_events
    op.create_table('kali_runtime_events',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('task_id', sa.String(), nullable=False),
    sa.Column('event_type', sa.String(), nullable=False),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('metadata_data', sa.JSON(), nullable=True),
    sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['task_id'], ['kali_tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kali_runtime_events_event_type'), 'kali_runtime_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_kali_runtime_events_task_id'), 'kali_runtime_events', ['task_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_kali_runtime_events_task_id'), table_name='kali_runtime_events')
    op.drop_index(op.f('ix_kali_runtime_events_event_type'), table_name='kali_runtime_events')
    op.drop_table('kali_runtime_events')
    
    op.drop_index(op.f('ix_kali_tasks_user_id'), table_name='kali_tasks')
    op.drop_index(op.f('ix_kali_tasks_project_id'), table_name='kali_tasks')
    op.drop_index(op.f('ix_kali_tasks_parent_task_id'), table_name='kali_tasks')
    op.drop_table('kali_tasks')
    
    op.drop_index(op.f('ix_kali_projects_user_id'), table_name='kali_projects')
    op.drop_table('kali_projects')
