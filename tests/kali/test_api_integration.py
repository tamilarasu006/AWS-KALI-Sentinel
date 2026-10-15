import os
# Must be set before importing app modules that load auth_routes at import time
os.environ.setdefault("JWT_SECRET", "test-secret-for-pytest-only")

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from OpenDEMON.server.app import create_app
from OpenDEMON.kali.orchestration import KALIOrchestrator

@pytest.fixture
def mock_engine():
    engine = MagicMock()
    engine.generate.return_value = {"content": "Mock OpenDEMON Response", "usage": {}}
    return engine

@pytest.fixture
def client_no_kali(mock_engine, monkeypatch):
    monkeypatch.setenv("KALI_ENABLED", "false")
    app = create_app(engine=mock_engine, model="opendemon-model")
    return TestClient(app)

@pytest.fixture
def client_with_kali(mock_engine, monkeypatch):
    monkeypatch.setenv("KALI_ENABLED", "true")
    app = create_app(engine=mock_engine, model="kali-model")
    
    # Mock the KALIOrchestrator to avoid hitting real model logic
    mock_orch = AsyncMock(spec=KALIOrchestrator)
    mock_orch.run.return_value = "Mock KALI Response"
    app.state.kali_orchestrator = mock_orch
    
    return TestClient(app), mock_orch

def test_chat_without_kali(client_no_kali):
    response = client_no_kali.post(
        "/v1/chat/completions",
        json={"model": "opendemon-model", "messages": [{"role": "user", "content": "Hello"}]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "Mock OpenDEMON Response" in data["choices"][0]["message"]["content"]

def test_chat_with_kali(client_with_kali):
    client, mock_orch = client_with_kali
    response = client.post(
        "/v1/chat/completions",
        json={"model": "kali-model", "messages": [{"role": "user", "content": "Hello KALI"}]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "Mock KALI Response" in data["choices"][0]["message"]["content"]
    mock_orch.run.assert_called_once()
    
def test_kali_health_disabled(client_no_kali):
    response = client_no_kali.get("/api/kali/health")
    # Will be 404 because the router is not mounted when KALI_ENABLED is false? 
    # Wait, the app.py mounts the router regardless of KALI_ENABLED, and the route itself checks `os.environ.get("KALI_ENABLED")`. Let's test that logic.
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "disabled"
    assert data["enabled"] is False

def test_kali_health_enabled(client_with_kali):
    client, _ = client_with_kali
    response = client.get("/api/kali/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["enabled"] is True
    assert data["engine"] == "kali"

def test_kali_models_disabled(client_no_kali):
    response = client_no_kali.get("/api/kali/models")
    assert response.status_code == 404

def test_kali_models_enabled(client_with_kali):
    client, _ = client_with_kali
    response = client.get("/api/kali/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) > 0
