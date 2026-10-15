import pytest
from fastapi.testclient import TestClient

import OpenDEMON.engine
from OpenDEMON.engine._discovery import discover_engines, get_engine
from OpenDEMON.core.config import DEMONConfig
from OpenDEMON.engine.kali import KALIEngine
from OpenDEMON.server.app import create_app
from OpenDEMON.kali.model.kali_model import KALIModel
from OpenDEMON.kali.model.config import KALIModelConfig
from OpenDEMON.kali import get_registry

@pytest.fixture(autouse=True)
def setup_kali():
    from OpenDEMON.core.registry import EngineRegistry
    EngineRegistry.register_value("kali", KALIEngine)
    
    registry = get_registry()
    registry._models.clear()
    
    config = KALIModelConfig(model_name="test-kali-model", model_path="/path")
    model = KALIModel(config)
    model.load()
    registry.register_model("test-kali-model", model)
    yield
    registry._models.clear()
    try:
        del EngineRegistry._entries()["kali"]
    except KeyError:
        pass

def test_discovery_finds_kali():
    config = DEMONConfig()
    engines = dict(discover_engines(config))
    assert "kali" in engines
    assert isinstance(engines["kali"], KALIEngine)

def test_get_engine_resolves_kali():
    config = DEMONConfig()
    result = get_engine(config, engine_key="kali", model="test-kali-model")
    assert result is not None
    key, engine = result
    assert key == "kali"
    assert isinstance(engine, KALIEngine)

def test_api_routes_with_kali():
    config = DEMONConfig()
    result = get_engine(config, engine_key="kali", model="test-kali-model")
    assert result is not None
    _, engine = result
    
    app = create_app(engine, "test-kali-model")
    client = TestClient(app)
    
    # Test models endpoint
    resp = client.get("/v1/models")
    assert resp.status_code == 200
    models = resp.json()["data"]
    assert any(m["id"] == "test-kali-model" for m in models)
    
    # Test generation routing
    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "test-kali-model",
            "messages": [{"role": "user", "content": "Hello"}]
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "KALI Generated Output" in data["choices"][0]["message"]["content"]
