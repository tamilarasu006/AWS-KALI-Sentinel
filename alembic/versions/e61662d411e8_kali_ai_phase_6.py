"""KALI AI Phase 6

Revision ID: e61662d411e8
Revises: 0785869619ba
Create Date: 2026-09-11 21:05:00.692837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e61662d411e8'
down_revision: Union[str, Sequence[str], None] = '0785869619ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from pgvector.sqlalchemy import Vector

def upgrade() -> None:
    """Upgrade schema."""
    # Create new tables
    op.create_table(
        'model_runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('model_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('metrics_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_runs_model_id'), 'model_runs', ['model_id'], unique=False)
    op.create_index(op.f('ix_model_runs_user_id'), 'model_runs', ['user_id'], unique=False)
    op.create_index(op.f('ix_model_runs_created_at'), 'model_runs', ['created_at'], unique=False)

    op.create_table(
        'model_versions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('version_tag', sa.String(), nullable=False),
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_versions_model_name'), 'model_versions', ['model_name'], unique=False)
    op.create_index(op.f('ix_model_versions_version_tag'), 'model_versions', ['version_tag'], unique=False)
    op.create_index(op.f('ix_model_versions_created_at'), 'model_versions', ['created_at'], unique=False)

    op.create_table(
        'embeddings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('reference_id', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(dim=768), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_embeddings_reference_id'), 'embeddings', ['reference_id'], unique=False)
    op.create_index(op.f('ix_embeddings_created_at'), 'embeddings', ['created_at'], unique=False)
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("CREATE INDEX idx_embeddings_embedding ON embeddings USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)")

    # Alter agent_runs
    op.add_column('agent_runs', sa.Column('model_id', sa.String(), nullable=True))
    op.add_column('agent_runs', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.create_index(op.f('ix_agent_runs_model_id'), 'agent_runs', ['model_id'], unique=False)

    # Add standard created_at indexes to existing tables
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)
    op.create_index(op.f('ix_conversations_created_at'), 'conversations', ['created_at'], unique=False)
    op.create_index(op.f('ix_messages_created_at'), 'messages', ['created_at'], unique=False)
    op.create_index(op.f('ix_memories_created_at'), 'memories', ['created_at'], unique=False)
    op.create_index(op.f('ix_documents_created_at'), 'documents', ['created_at'], unique=False)
    op.create_index(op.f('ix_agents_created_at'), 'agents', ['created_at'], unique=False)
    op.create_index(op.f('ix_agent_runs_created_at'), 'agent_runs', ['created_at'], unique=False)
    op.create_index(op.f('ix_tool_calls_created_at'), 'tool_calls', ['created_at'], unique=False)

    # Add HNSW pgvector indexes
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("CREATE INDEX idx_memories_embedding ON memories USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)")
        op.execute("CREATE INDEX idx_document_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)")


def downgrade() -> None:
    """Downgrade schema."""
    # Drop HNSW pgvector indexes
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("DROP INDEX IF EXISTS idx_document_chunks_embedding")
        op.execute("DROP INDEX IF EXISTS idx_memories_embedding")

    # Drop created_at indexes
    op.drop_index(op.f('ix_tool_calls_created_at'), table_name='tool_calls')
    op.drop_index(op.f('ix_agent_runs_created_at'), table_name='agent_runs')
    op.drop_index(op.f('ix_agents_created_at'), table_name='agents')
    op.drop_index(op.f('ix_documents_created_at'), table_name='documents')
    op.drop_index(op.f('ix_memories_created_at'), table_name='memories')
    op.drop_index(op.f('ix_messages_created_at'), table_name='messages')
    op.drop_index(op.f('ix_conversations_created_at'), table_name='conversations')
    op.drop_index(op.f('ix_users_created_at'), table_name='users')

    # Drop agent_runs modification
    op.drop_index(op.f('ix_agent_runs_model_id'), table_name='agent_runs')
    op.drop_column('agent_runs', 'model_id')

    # Drop embeddings
    op.execute("DROP INDEX IF EXISTS idx_embeddings_embedding")
    op.drop_index(op.f('ix_embeddings_created_at'), table_name='embeddings')
    op.drop_index(op.f('ix_embeddings_reference_id'), table_name='embeddings')
    op.drop_table('embeddings')

    # Drop model_versions
    op.drop_index(op.f('ix_model_versions_created_at'), table_name='model_versions')
    op.drop_index(op.f('ix_model_versions_version_tag'), table_name='model_versions')
    op.drop_index(op.f('ix_model_versions_model_name'), table_name='model_versions')
    op.drop_table('model_versions')

    # Drop model_runs
    op.drop_index(op.f('ix_model_runs_created_at'), table_name='model_runs')
    op.drop_index(op.f('ix_model_runs_user_id'), table_name='model_runs')
    op.drop_index(op.f('ix_model_runs_model_id'), table_name='model_runs')
    op.drop_table('model_runs')
