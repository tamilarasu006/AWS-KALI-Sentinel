import asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock

from OpenDEMON.server.kali_unified_routes import router

def run():
    print("Testing Unified KALI API...")
    
    app = FastAPI()
    app.include_router(router)
    
    runtime_mock = MagicMock()
    runtime_mock.rag_pipeline = AsyncMock()
    runtime_mock.rag_pipeline.embedding_provider = AsyncMock()
    runtime_mock.rag_pipeline.embedding_provider.embed.return_value = [0.1, 0.2, 0.3]
    runtime_mock.rag_pipeline.build_context = MagicMock(return_value="Retrieved Context")
    runtime_mock.rag_pipeline.retrieve.return_value = ["chunk1"]
    
    runtime_mock.memory_manager = AsyncMock()
    runtime_mock.memory_manager.retrieve.return_value = [{"content": "Memory entry"}]
    
    runtime_mock.agent_manager = MagicMock()
    agent_mock = MagicMock()
    agent_mock.name = "TestAgent"
    agent_mock.description = "Test Desc"
    agent_mock.risk_level.name = "LOW"
    runtime_mock.agent_manager.registry.list_all.return_value = [agent_mock]
    
    runtime_mock.tool_registry = MagicMock()
    tool_mock = MagicMock()
    tool_mock.name = "TestTool"
    tool_mock.description = "Test Desc"
    tool_mock.category = "Test"
    tool_mock.risk_level.name = "LOW"
    tool_mock.input_schema = MagicMock()
    tool_mock.input_schema.model_json_schema.return_value = {"type": "object"}
    runtime_mock.tool_registry.list.return_value = [tool_mock]
    
    app.state.kali_runtime = runtime_mock
    
    client = TestClient(app)
    
    print("\n--- Testing Embeddings ---")
    resp = client.post("/api/kali/v1/embeddings", json={"input": "test text"})
    print(resp.json())
    assert resp.status_code == 200
    
    print("\n--- Testing RAG Query ---")
    resp = client.post("/api/kali/v1/rag/query", json={"project_id": "proj_123", "query": "Find the secret."})
    print(resp.json())
    assert resp.status_code == 200
    
    print("\n--- Testing Agents List ---")
    resp = client.get("/api/kali/v1/agents")
    print(resp.json())
    assert resp.status_code == 200
    
    print("\nALL TESTS PASSED MANUALLY!")

if __name__ == "__main__":
    run()
