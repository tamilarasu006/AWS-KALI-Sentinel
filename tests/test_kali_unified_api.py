import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock

from OpenDEMON.server.kali_unified_routes import router

@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    
    # Mock KALI Runtime
    runtime_mock = MagicMock()
    runtime_mock.rag_pipeline = AsyncMock()
    runtime_mock.rag_pipeline.embedding_provider = AsyncMock()
    runtime_mock.rag_pipeline.embedding_provider.embed.return_value = [0.1, 0.2, 0.3]
    runtime_mock.rag_pipeline.build_context = MagicMock(return_value="Retrieved Context")
    runtime_mock.rag_pipeline.retrieve.return_value = ["chunk1"]
    
    runtime_mock.memory_manager = AsyncMock()
    runtime_mock.memory_manager.retrieve.return_value = [{"content": "Memory entry"}]
    
    # Mock Agent and Tool registries
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
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_embeddings_route(client):
    response = client.post("/api/kali/v1/embeddings", json={"input": "test text"})
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"][0]["embedding"] == [0.1, 0.2, 0.3]

def test_memories_route(client):
    # GET
    response = client.get("/api/kali/v1/memories?user_id=test_user")
    assert response.status_code == 200
    assert response.json()["memories"][0]["content"] == "Memory entry"
    
    # POST
    response = client.post("/api/kali/v1/memories", json={
        "user_id": "test_user",
        "content": "New memory",
        "memory_type": "long_term"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_rag_query_route(client):
    response = client.post("/api/kali/v1/rag/query", json={
        "project_id": "proj_123",
        "query": "Where is the file?"
    })
    assert response.status_code == 200
    assert response.json()["context"] == "Retrieved Context"
    assert response.json()["chunks_retrieved"] == 1

def test_agents_route(client):
    response = client.get("/api/kali/v1/agents")
    assert response.status_code == 200
    assert response.json()["agents"][0]["name"] == "TestAgent"

def test_tools_route(client):
    response = client.get("/api/kali/v1/tools")
    assert response.status_code == 200
    assert response.json()["tools"][0]["name"] == "TestTool"
    assert response.json()["tools"][0]["input_schema"] == {"type": "object"}
