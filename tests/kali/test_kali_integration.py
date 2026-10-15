"""Integration tests for KALI architecture through the Engine interface."""

import pytest
import torch
from OpenDEMON.kali.model.config import KALIModelConfig
from OpenDEMON.kali.model.kali_model import KALIModel
from OpenDEMON.engine.kali import KALIEngine
from OpenDEMON.core.registry import EngineRegistry

@pytest.fixture
def small_config():
    """A small configuration for fast testing."""
    return KALIModelConfig(
        model_name="test-integration-model",
        model_path="/dev/null",
        context_length=64,
        hidden_size=64,
        num_layers=2,
        num_attention_heads=2,
        num_kv_heads=2,
        intermediate_size=128,
        vocab_size=256, # Enough for ASCII
        dtype="float32",
        device="cpu"
    )

@pytest.fixture
def kali_engine(small_config):
    """Provides a KALIEngine loaded with a small model."""
    model = KALIModel(small_config)
    model.load()
    
    # Register the model globally in the registry
    from OpenDEMON.kali import get_registry
    registry = get_registry()
    registry.register_model("test-integration-model", model)
    
    engine = KALIEngine()
    
    yield engine
    
    # Cleanup
    if "test-integration-model" in registry._models:
        del registry._models["test-integration-model"]

def test_generate_deterministic(kali_engine):
    """Test that generation with temp=0 yields deterministic output."""
    from OpenDEMON.core.types import Message, Role
    
    output1 = kali_engine.generate(
        [Message(role=Role.USER, content="Hello")],
        model="test-integration-model",
        max_new_tokens=5,
        temperature=0.0
    )
    
    output2 = kali_engine.generate(
        [Message(role=Role.USER, content="Hello")],
        model="test-integration-model",
        max_new_tokens=5,
        temperature=0.0
    )
    
    assert len(output1) > 0
    assert output1["content"] == output2["content"]

def test_generate_seeded(kali_engine):
    """Test that generation with a specific seed yields deterministic output."""
    from OpenDEMON.core.types import Message, Role
    
    output1 = kali_engine.generate(
        [Message(role=Role.USER, content="Hello")],
        model="test-integration-model",
        max_new_tokens=5,
        temperature=1.0,
        seed=42
    )
    
    output2 = kali_engine.generate(
        [Message(role=Role.USER, content="Hello")],
        model="test-integration-model",
        max_new_tokens=5,
        temperature=1.0,
        seed=42
    )
    
    assert len(output1) > 0
    assert output1["content"] == output2["content"]

@pytest.mark.asyncio
async def test_generate_streaming(kali_engine):
    """Test that streaming yields tokens dynamically."""
    from OpenDEMON.core.types import Message, Role
    
    stream_gen = kali_engine.stream(
        [Message(role=Role.USER, content="Hello")],
        model="test-integration-model",
        max_new_tokens=5,
        temperature=0.0
    )
    
    chunks = []
    async for chunk in stream_gen:
        chunks.append(chunk)
    
    # max_new_tokens is 5, we should get exactly 5 chunks back
    assert len(chunks) == 5
    
    # They should combine to the same string as the normal generate
    output_streamed = "".join(chunks)
    
    output_normal = kali_engine.generate(
        [Message(role=Role.USER, content="Hello")],
        model="test-integration-model",
        max_new_tokens=5,
        temperature=0.0
    )
    
    assert output_streamed == output_normal["content"]

def test_stop_tokens(kali_engine):
    """Test that generation respects stop tokens."""
    from OpenDEMON.core.types import Message, Role
    
    # Let's get 5 deterministic tokens
    output = kali_engine.generate(
        [Message(role=Role.USER, content="Test")],
        model="test-integration-model",
        max_new_tokens=5,
        temperature=0.0
    )
    
    content = output["content"]
    
    if len(content) > 1:
        # Use the first emitted char as a stop token
        stop_char = content[0]
        
        stopped_output = kali_engine.generate(
            [Message(role=Role.USER, content="Test")],
            model="test-integration-model",
            max_new_tokens=5,
            temperature=0.0,
            stop_tokens=[stop_char]
        )
        
        stopped_content = stopped_output["content"]
        
        # It should have stopped at the first char
        assert len(stopped_content) <= len(content)
        assert stopped_content.endswith(stop_char)
