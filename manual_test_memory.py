import asyncio
from unittest.mock import AsyncMock

from OpenDEMON.kali.core.context_builder import KALIContextBuilder, ContextConfig

async def run():
    print("Testing Memory and RAG Context Builder...")
    
    mock_memory = AsyncMock()
    async def mock_retrieve(user_id, memory_type, **kwargs):
        if memory_type == "preferences":
            return "User prefers concise answers."
        if memory_type == "short_term":
            return [{"role": "user", "content": "What is OpenDEMON?"}]
        if memory_type == "episodic":
            return [{"content": "Scanned network 10.0.0.1"}]
        return None
    mock_memory.retrieve.side_effect = mock_retrieve
    
    from unittest.mock import MagicMock
    mock_rag = AsyncMock()
    mock_rag.retrieve.return_value = ["doc_chunk_1"]
    mock_rag.build_context = MagicMock(return_value="OpenDEMON is an open-source AI platform.")
    
    builder = KALIContextBuilder(mock_memory, mock_rag)
    
    print("\n--- Test 1: Full Context Construction ---")
    prompt = "Tell me more about it."
    result = await builder.build_context(prompt, "user123", "proj456", "conv789")
    
    print("--- ASSEMBLED CONTEXT ---")
    print(result)
    print("-------------------------")
    
    assert "User prefers concise answers." in result
    assert "Scanned network 10.0.0.1" in result
    assert "OpenDEMON is an open-source AI platform." in result
    assert "<UNTRUSTED_DOCUMENTS>" in result
    
    print("\n--- Test 2: Project Isolation Enforcement ---")
    args, kwargs = mock_rag.retrieve.call_args
    assert kwargs.get("metadata_filter") == {"project_id": "proj456"}
    print(f"RAG Filter applied: {kwargs.get('metadata_filter')}")
    
    print("\nALL TESTS PASSED MANUALLY!")

if __name__ == "__main__":
    asyncio.run(run())
