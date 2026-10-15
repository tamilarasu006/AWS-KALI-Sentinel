import pytest

from OpenDEMON.kali.model.config import KALIModelConfig
from OpenDEMON.kali.model.kali_model import KALIModel


def _tiny_config():
    """Return a tiny config for fast CPU tests. Default config is LLaMA-7B scale."""
    return KALIModelConfig(
        model_name="test",
        model_path="/path",
        hidden_size=64,
        num_layers=2,
        num_attention_heads=4,
        intermediate_size=128,
        vocab_size=256,
        context_length=32,
        dtype="float32",
    )


def test_kalimodel_lifecycle():
    model = KALIModel(_tiny_config())

    assert not model.health()
    model.load()
    assert model.health()

    output = model.generate("Hello", max_new_tokens=3)
    assert isinstance(output, str)
    assert len(output) > 0  # Should produce some decoded tokens

    stream_output = list(model.stream("Hello", max_new_tokens=3))
    assert len(stream_output) > 0  # Should yield at least one token chunk

    metadata = model.metadata()
    assert metadata["name"] == "test"
    assert metadata["loaded"] is True

    model.unload()
    assert not model.health()

def test_kalimodel_unloaded_raises():
    model = KALIModel(_tiny_config())

    with pytest.raises(RuntimeError):
        model.generate("test")

    with pytest.raises(RuntimeError):
        list(model.stream("test"))
