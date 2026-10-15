import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from OpenDEMON.kali.core.context_builder import KALIContextBuilder, ContextConfig

@pytest.fixture
def mock_memory():
    manager = AsyncMock()
    # Return dummy memory based on type
    async def mock_retrieve(user_id, memory_type, **kwargs):
        if memory_type == "preferences":
            return "Prefers Python"
        if memory_type == "short_term":
            return [{"role": "user", "content": "Hi"}]
        if memory_type == "episodic":
            return [{"content": "Created a file"}]
        return None
    manager.retrieve.side_effect = mock_retrieve
    return manager

@pytest.fixture
def mock_rag():
    pipeline = AsyncMock()
    pipeline.retrieve.return_value = ["doc1", "doc2"]
    pipeline.build_context.return_value = "Contents of doc1 and doc2"
    return pipeline

@pytest.mark.asyncio
async def test_context_builder_integration(mock_memory, mock_rag):
    builder = KALIContextBuilder(mock_memory, mock_rag)
    
    prompt = "How do I do this?"
    result = await builder.build_context(prompt, "u1", "p1", "c1")
    
    # Assert Memory is included
    assert "User Preferences: Prefers Python" in result
    assert "user: Hi" in result
    assert "Created a file" in result
    
    # Assert RAG is included with security wrappers
    assert "<WARNING>" in result
    assert "<UNTRUSTED_DOCUMENTS>" in result
    assert "Contents of doc1 and doc2" in result
    assert "</UNTRUSTED_DOCUMENTS>" in result
    
    # Assert original prompt is preserved
    assert f"User Query: {prompt}" in result

@pytest.mark.asyncio
async def test_context_limits(mock_memory, mock_rag):
    # Make RAG return a massive string
    mock_rag.build_context.return_value = "A" * 10000
    
    builder = KALIContextBuilder(mock_memory, mock_rag)
    config = ContextConfig(max_rag_tokens=100) # Should limit to ~400 chars
    
    result = await builder.build_context("Test", "u1", "p1", "c1", config)
    
    # RAG chunk should be truncated
    assert "[TRUNCATED]" in result
    # Entire result shouldn't exceed memory + rag limits drastically
    assert len(result) < 2000 

@pytest.mark.asyncio
async def test_isolation_enforcement(mock_memory, mock_rag):
    builder = KALIContextBuilder(mock_memory, mock_rag)
    await builder.build_context("Test", "u1", "p1", "c1")
    
    # Assert RAG retrieve was called with project_id filter
    mock_rag.retrieve.assert_called_once()
    args, kwargs = mock_rag.retrieve.call_args
    assert kwargs.get("metadata_filter") == {"project_id": "p1"}
    
    # Assert Memory retrieve was called with user_id
    mock_memory.retrieve.assert_any_call("u1", memory_type="preferences")
