from OpenDEMON.kali.model.config import KALIModelConfig


def test_kalimodelconfig_defaults():
    config = KALIModelConfig(
        model_name="test-model",
        model_path="/dummy/path"
    )
    assert config.model_name == "test-model"
    assert config.model_path == "/dummy/path"
    assert config.tokenizer_path is None
    assert config.context_length == 4096
    assert config.hidden_size == 4096
    assert config.num_layers == 32
    assert config.num_attention_heads == 32
    # num_kv_heads should default to num_attention_heads
    assert config.num_kv_heads == 32
    assert config.intermediate_size == 11008
    assert config.vocab_size == 32000
    assert config.dtype == "float16"
    assert config.device == "cpu"

def test_kalimodelconfig_custom():
    config = KALIModelConfig(
        model_name="custom-model",
        model_path="/custom/path",
        num_attention_heads=16,
        num_kv_heads=4
    )
    assert config.num_attention_heads == 16
    assert config.num_kv_heads == 4
