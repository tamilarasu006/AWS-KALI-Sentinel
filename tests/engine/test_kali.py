import pytest
from unittest.mock import patch, MagicMock
from typing import AsyncIterator

from OpenDEMON.core.types import Message, Role
from OpenDEMON.engine.kali import KALIEngine
from OpenDEMON.kali.model.kali_model import KALIModel
from OpenDEMON.kali.model.config import KALIModelConfig
from OpenDEMON.kali import get_registry

@pytest.fixture(autouse=True)
def clean_registry():
    """Ensure the registry is clean before and after each test."""
    registry = get_registry()
    registry._models.clear()
    registry._default_model_name = None
    yield
    registry._models.clear()
    registry._default_model_name = None

@pytest.fixture
def mock_kali_model():
    config = KALIModelConfig(
        model_name="mock-kali", 
        model_path="/dev/null",
        context_length=64,
        hidden_size=64,
        num_layers=2,
        num_attention_heads=2,
        num_kv_heads=2,
        intermediate_size=128,
        vocab_size=256,
    )
    model = KALIModel(config)
    get_registry().register_model("mock-kali", model)
    return model

def test_engine_initialization():
    engine = KALIEngine()
    assert engine.engine_id == "kali"
    assert engine.health() is True
    assert "kali" in engine.list_models()

def test_engine_list_models(mock_kali_model):
    engine = KALIEngine()
    assert "mock-kali" in engine.list_models()

def test_engine_can_serve(mock_kali_model):
    engine = KALIEngine()
    assert engine.can_serve("mock-kali") is True
    assert engine.can_serve("non-existent") is False

def test_engine_generate(mock_kali_model):
    engine = KALIEngine()
    messages = [Message(role=Role.USER, content="Hello")]
    
    mock_kali_model.load() # Make it healthy
    result = engine.generate(messages, model="mock-kali")
    
    assert "content" in result
    assert "usage" in result
    assert isinstance(result["content"], str)
    assert len(result["content"]) > 0

@pytest.mark.asyncio
async def test_engine_stream(mock_kali_model):
    engine = KALIEngine()
    messages = [Message(role=Role.USER, content="Hello")]
    
    mock_kali_model.load()
    chunks = []
    async for chunk in engine.stream(messages, model="mock-kali"):
        chunks.append(chunk)
        
    assert len(chunks) > 0
    assert isinstance(chunks[0], str)

def test_engine_prepare_loads_model(mock_kali_model):
    engine = KALIEngine()
    assert not mock_kali_model.health()
    engine.prepare("mock-kali")
    assert mock_kali_model.health()

def test_engine_close_unloads_models(mock_kali_model):
    engine = KALIEngine()
    engine.prepare("mock-kali")
    assert mock_kali_model.health()
    engine.close()
    assert not mock_kali_model.health()
