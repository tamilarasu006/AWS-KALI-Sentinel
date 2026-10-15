import pytest
import torch

from OpenDEMON.kali.model.config import KALIModelConfig
from OpenDEMON.kali.architecture.transformer import KALITransformer
from OpenDEMON.kali.architecture.cache import KVCache
from OpenDEMON.kali.architecture.normalization import RMSNorm
from OpenDEMON.kali.architecture.mlp import SwiGLU

@pytest.fixture
def small_config():
    """A small configuration for fast testing."""
    return KALIModelConfig(
        model_name="test-kali-arch",
        model_path="/dev/null",
        context_length=128,
        hidden_size=256,
        num_layers=2,
        num_attention_heads=8,
        num_kv_heads=2,
        intermediate_size=512,
        vocab_size=1000,
        dtype="float32",
        device="cpu"
    )

def test_model_construction(small_config):
    """Test that the model constructs without error."""
    model = KALITransformer(small_config)
    assert model.config.hidden_size == 256
    assert len(model.layers) == 2
    assert model.lm_head.out_features == 1000

def test_forward_pass_output_shape(small_config):
    """Test that the forward pass produces the correct shape."""
    model = KALITransformer(small_config)
    batch_size = 2
    seq_len = 10
    
    input_ids = torch.randint(0, small_config.vocab_size, (batch_size, seq_len))
    logits = model(input_ids)
    
    assert logits.shape == (batch_size, seq_len, small_config.vocab_size)

def test_causal_masking(small_config):
    """Test that future tokens do not affect past tokens."""
    model = KALITransformer(small_config)
    model.eval() # Disable dropout if any exists, though we have none
    
    batch_size = 1
    seq_len = 5
    
    input_ids = torch.randint(0, small_config.vocab_size, (batch_size, seq_len))
    
    # Run full sequence
    with torch.no_grad():
        logits_full = model(input_ids)
        
    # Run only prefix
    with torch.no_grad():
        logits_prefix = model(input_ids[:, :3])
        
    # The output for the first 3 tokens should be exactly the same
    # regardless of whether the sequence is 3 or 5 tokens long.
    assert torch.allclose(logits_full[:, :3, :], logits_prefix, atol=1e-5)

def test_kv_cache(small_config):
    """Test KV caching logic."""
    model = KALITransformer(small_config)
    model.eval()
    
    batch_size = 1
    head_dim = small_config.hidden_size // small_config.num_attention_heads
    
    kv_caches = [
        KVCache(
            batch_size=batch_size,
            max_seq_len=small_config.context_length,
            num_kv_heads=small_config.num_kv_heads,
            head_dim=head_dim,
            device=torch.device("cpu"),
            dtype=torch.float32,
        )
        for _ in range(small_config.num_layers)
    ]
    
    # First token
    input_ids_1 = torch.randint(0, small_config.vocab_size, (batch_size, 1))
    
    with torch.no_grad():
        logits_1 = model(input_ids_1, kv_caches=kv_caches)
        
    assert kv_caches[0].current_seq_len == 1
    
    # Second token
    input_ids_2 = torch.randint(0, small_config.vocab_size, (batch_size, 1))
    
    with torch.no_grad():
        logits_2 = model(input_ids_2, kv_caches=kv_caches)
        
    assert kv_caches[0].current_seq_len == 2
    
    # Compare with non-cached forward pass of both tokens
    input_ids_full = torch.cat([input_ids_1, input_ids_2], dim=1)
    
    with torch.no_grad():
        logits_full = model(input_ids_full)
        
    # Output of the second token should be the same
    assert torch.allclose(logits_2[:, 0, :], logits_full[:, 1, :], atol=1e-4)

def test_different_sequence_lengths(small_config):
    """Test with different sequence lengths up to context length."""
    model = KALITransformer(small_config)
    batch_size = 1
    
    for seq_len in [1, 7, 33, 128]:
        input_ids = torch.randint(0, small_config.vocab_size, (batch_size, seq_len))
        logits = model(input_ids)
        assert logits.shape == (batch_size, seq_len, small_config.vocab_size)

def test_cpu_inference(small_config):
    """Test that model works entirely on CPU."""
    model = KALITransformer(small_config).to("cpu")
    input_ids = torch.randint(0, small_config.vocab_size, (1, 10)).to("cpu")
    logits = model(input_ids)
    assert logits.device.type == "cpu"
    assert not torch.isnan(logits).any()

def test_rmsnorm():
    """Test RMSNorm standalone behavior."""
    norm = RMSNorm(16)
    x = torch.randn(2, 5, 16)
    y = norm(x)
    assert y.shape == x.shape
    # Check that root mean square is approx 1
    rms = torch.sqrt(torch.mean(y**2, dim=-1))
    assert torch.allclose(rms, torch.ones_like(rms), atol=1e-3)

def test_swiglu():
    """Test SwiGLU standalone behavior."""
    mlp = SwiGLU(16, 32)
    x = torch.randn(2, 5, 16)
    y = mlp(x)
    assert y.shape == (2, 5, 16)
