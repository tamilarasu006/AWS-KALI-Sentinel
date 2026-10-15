import pytest
from OpenDEMON.kali.tokenizer import DummyKALITokenizer, SpecialTokens
from OpenDEMON.kali.model.config import KALIModelConfig
from OpenDEMON.kali.model.kali_model import KALIModel

def test_dummy_tokenizer_encode_decode():
    tokenizer = DummyKALITokenizer(vocab_size=32000)
    text = "Hello KALI AI!"
    
    encoded = tokenizer.encode(text, add_bos=True)
    assert len(encoded) == len(text) + 1
    assert encoded[0] == tokenizer.special_tokens.bos_token_id
    
    decoded = tokenizer.decode(encoded, skip_special_tokens=True)
    assert decoded == text
    
def test_dummy_tokenizer_encode_decode_batch():
    tokenizer = DummyKALITokenizer(vocab_size=32000)
    texts = ["Batch 1", "Batch 2"]
    
    encoded_batch = tokenizer.encode_batch(texts, add_bos=True)
    assert len(encoded_batch) == 2
    
    decoded_batch = tokenizer.decode_batch(encoded_batch, skip_special_tokens=True)
    assert decoded_batch == texts

def test_special_tokens():
    tokenizer = DummyKALITokenizer(vocab_size=32000)
    assert tokenizer.token_to_id("<bos>") == 0
    assert tokenizer.id_to_token(1) == "<eos>"

def test_vocab_size_validation():
    # Model expects 32000, but we force tokenizer to 1000
    config = KALIModelConfig(
        model_name="test",
        model_path=".",
        vocab_size=32000,
        context_length=64,
        hidden_size=64,
        num_layers=1,
        num_attention_heads=1,
        num_kv_heads=1,
        intermediate_size=128
    )
    
    model = KALIModel(config)
    
    # We monkey patch the DummyKALITokenizer inside the model's load
    # to return a different vocab size to test validation
    
    import OpenDEMON.kali.model.kali_model
    original_dummy = OpenDEMON.kali.model.kali_model.DummyKALITokenizer
    
    class BadTokenizer(original_dummy):
        def vocab_size(self):
            return 1000
            
    OpenDEMON.kali.model.kali_model.DummyKALITokenizer = BadTokenizer
    
    try:
        with pytest.raises(ValueError, match="does not match model config"):
            model.load()
    finally:
        # Restore
        OpenDEMON.kali.model.kali_model.DummyKALITokenizer = original_dummy
