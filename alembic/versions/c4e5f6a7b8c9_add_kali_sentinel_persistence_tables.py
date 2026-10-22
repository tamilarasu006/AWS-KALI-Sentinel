"""Add KALI Sentinel persistence tables: security_requests, decisions, tool_executions, agent_memory

Revision ID: c4e5f6a7b8c9
Revises: be4990556a89
Create Date: 2026-10-16 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    Vector = None
    HAS_PGVECTOR = False

# revision identifiers, used by Alembic.
revision: str = 'c4e5f6a7b8c9'
down_revision: Union[str, None] = 'be4990556a89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Enable pgvector extension if PostgreSQL
    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. security_requests
    op.create_table(
        'security_requests',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=128), nullable=True),
        sa.Column('request_text', sa.Text(), nullable=False),
        sa.Column('target', sa.String(length=255), nullable=True),
        sa.Column('authorized', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_security_requests_session_id'), 'security_requests', ['session_id'], unique=False)
    op.create_index(op.f('ix_security_requests_created_at'), 'security_requests', ['created_at'], unique=False)

    # 2. decisions
    op.create_table(
        'decisions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('request_id', sa.String(length=36), nullable=False),
        sa.Column('decision', sa.String(length=64), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['request_id'], ['security_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_decisions_request_id'), 'decisions', ['request_id'], unique=False)
    op.create_index(op.f('ix_decisions_created_at'), 'decisions', ['created_at'], unique=False)

    # 3. tool_executions
    op.create_table(
        'tool_executions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('request_id', sa.String(length=36), nullable=False),
        sa.Column('tool_name', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('result', sa.JSON(), nullable=False),
        sa.Column('execution_latency_ms', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['request_id'], ['security_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tool_executions_request_id'), 'tool_executions', ['request_id'], unique=False)
    op.create_index(op.f('ix_tool_executions_created_at'), 'tool_executions', ['created_at'], unique=False)

    # 4. agent_memory
    embedding_col = Vector(768) if (is_postgres and HAS_PGVECTOR and Vector is not None) else sa.JSON()
    op.create_table(
        'agent_memory',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=128), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', embedding_col, nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_memory_session_id'), 'agent_memory', ['session_id'], unique=False)
    op.create_index(op.f('ix_agent_memory_created_at'), 'agent_memory', ['created_at'], unique=False)

    if is_postgres and HAS_PGVECTOR:
        try:
            op.execute("CREATE INDEX IF NOT EXISTS idx_agent_memory_embedding ON agent_memory USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);")
        except Exception:
            pass


def downgrade() -> None:
    op.drop_table('agent_memory')
    op.drop_table('tool_executions')
    op.drop_table('decisions')
    op.drop_table('security_requests')
