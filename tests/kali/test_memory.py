import pytest
import pytest_asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from OpenDEMON.database.base import Base
from OpenDEMON.database.models import User, Conversation, Message, Memory, UserProfile
from OpenDEMON.kali.memory.manager import MemoryManager
from OpenDEMON.kali.rag.embeddings import FakeEmbeddingProvider

# Use an in-memory SQLite database for testing SQLAlchemy Logic.
# Note: SQLite does not support pgvector, so for the semantic search test,
# we might need to mock or skip if SQLite, or use standard sorting if we implement a fallback.
# For strictly testing the python logic isolation, we can just test the SQL generation
# or mock the session execute.
# Let's create an async engine. Since Memory uses Vector, SQLite will crash if we try to create_all.
# To bypass, we mock the AsyncSession for Semantic Search, but use real SQLite for others?
# Actually, the user asked to not add a second vector DB, so we must just test the logic, maybe with mocks
# for the pgvector parts or rely on pytest-mock. 
# Let's use a pure mock session for these tests to avoid DB dependency issues in CI.

from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.fixture
def memory_manager(mock_session):
    return MemoryManager(mock_session)

@pytest.mark.asyncio
async def test_short_term_storage_and_retrieval(memory_manager, mock_session):
    # Test adding a message
    await memory_manager.short_term.add_message("user1", "conv1", "user", "Hello")
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()

    # Test retrieving
    mock_result = MagicMock()
    msg1 = Message(role="user", content="Hello")
    mock_result.scalars().all.return_value = [msg1]
    mock_session.execute.return_value = mock_result

    msgs = await memory_manager.retrieve("user1", memory_type="short_term", conversation_id="conv1")
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "Hello"

@pytest.mark.asyncio
async def test_long_term_storage_and_retrieval(memory_manager, mock_session):
    await memory_manager.store("user1", "Sky is blue", memory_type="long_term")
    mock_session.add.assert_called_once()
    
    mock_result = MagicMock()
    mem1 = Memory(user_id="user1", content="Sky is blue", metadata_json='{"type": "long_term"}')
    mock_result.scalars().all.return_value = [mem1]
    mock_session.execute.return_value = mock_result

    facts = await memory_manager.retrieve("user1", memory_type="long_term")
    assert len(facts) == 1
    assert facts[0] == "Sky is blue"

@pytest.mark.asyncio
async def test_semantic_search(memory_manager, mock_session):
    provider = FakeEmbeddingProvider(dimension=3)
    emb = provider.embed("test query")
    
    # Store
    await memory_manager.store("user1", "Semantic fact", memory_type="semantic", embedding=emb, metadata={"foo": "bar"})
    mock_session.add.assert_called_once()

    # Search
    mock_result = MagicMock()
    mem1 = Memory(content="Semantic fact", metadata_json='{"foo": "bar"}', created_at="2026-01-01")
    mock_result.scalars().all.return_value = [mem1]
    mock_session.execute.return_value = mock_result

    results = await memory_manager.search("user1", emb, top_k=1)
    assert len(results) == 1
    assert results[0]["content"] == "Semantic fact"
    assert results[0]["metadata"]["foo"] == "bar"

@pytest.mark.asyncio
async def test_user_isolation_update_delete(memory_manager, mock_session):
    # If memory doesn't belong to user, it should return False
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None # Not found for this user
    mock_session.execute.return_value = mock_result

    updated = await memory_manager.update("user2", "mem_id", "Hacked content")
    assert updated is False
    
    deleted = await memory_manager.delete("user2", "mem_id")
    assert deleted is False

@pytest.mark.asyncio
async def test_conversation_separation(memory_manager, mock_session):
    # Short-term memory retrieval should require conversation_id
    with pytest.raises(ValueError, match="requires conversation_id"):
        await memory_manager.retrieve("user1", memory_type="short_term")

@pytest.mark.asyncio
async def test_preferences(memory_manager, mock_session):
    # Test retrieving empty prefs
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    prefs = await memory_manager.retrieve("user1", memory_type="preferences")
    assert prefs == {}
    
    # Test updating prefs
    await memory_manager.preferences.update_preferences("user1", {"theme": "dark"})
    mock_session.commit.assert_called_once()
