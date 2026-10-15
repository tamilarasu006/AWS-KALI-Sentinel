import pytest
import os
import tempfile
from OpenDEMON.kali.tokenizer.bpe_tokenizer import KALIBPETokenizer

@pytest.fixture
def tokenizer():
    return KALIBPETokenizer(vocab_size=1000)

def test_tokenizer_initialization(tokenizer):
    assert tokenizer.vocab_size() == 1000
    assert tokenizer.special_tokens.bos_token == "<bos>"
    assert tokenizer.special_tokens.user_token == "<user>"
    assert tokenizer.special_tokens.assistant_token == "<assistant>"
    assert tokenizer.special_tokens.tool_token == "<tool>"
    assert tokenizer.special_tokens.pad_token_id is not None

def test_encode_decode_english(tokenizer):
    text = "Hello world! This is a test."
    encoded = tokenizer.encode(text, add_bos=False)
    decoded = tokenizer.decode(encoded)
    # ByteLevel decoding may strip or modify leading space slightly depending on configuration, 
    # but basic roundtrip of the words should be intact.
    assert "Hello" in decoded
    assert "world" in decoded

def test_special_tokens_preserved(tokenizer):
    # Test that special tokens can be encoded and decoded correctly
    user_id = tokenizer.special_tokens.user_token_id
    text = "<user> Write some code."
    encoded = tokenizer.encode(text, add_bos=False)
    assert user_id in encoded
    
    # decode with skip_special_tokens=False
    decoded = tokenizer.decode(encoded, skip_special_tokens=False)
    assert "<user>" in decoded

def test_skip_special_tokens(tokenizer):
    text = "<user> Hello <assistant>"
    encoded = tokenizer.encode(text, add_bos=False)
    decoded = tokenizer.decode(encoded, skip_special_tokens=True)
    assert "<user>" not in decoded
    assert "<assistant>" not in decoded

def test_batch_encode_decode(tokenizer):
    texts = ["Hello", "World", "JSON data: {\"key\": \"value\"}"]
    batch_enc = tokenizer.encode_batch(texts, add_bos=False)
    assert len(batch_enc) == 3
    
    batch_dec = tokenizer.decode_batch(batch_enc, skip_special_tokens=True)
    assert "Hello" in batch_dec[0]
    assert "World" in batch_dec[1]
    assert "JSON data" in batch_dec[2]

def test_code_urls_numbers(tokenizer):
    text = "def foo(): return 42\n# https://example.com"
    encoded = tokenizer.encode(text, add_bos=False)
    decoded = tokenizer.decode(encoded)
    assert "def foo()" in decoded
    assert "42" in decoded
    assert "https://example.com" in decoded

def test_save_load_vocabulary(tokenizer):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "tokenizer.json")
        tokenizer.save(path)
        assert os.path.exists(path)
        
        # Reload
        loaded_tokenizer = KALIBPETokenizer(vocab_size=1000, tokenizer_path=path)
        assert loaded_tokenizer.vocab_size() == 1000
        assert loaded_tokenizer.special_tokens.bos_token_id == tokenizer.special_tokens.bos_token_id
