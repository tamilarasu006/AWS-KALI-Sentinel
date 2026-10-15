import pytest
import torch
import os
import tempfile
from OpenDEMON.kali.model.config import get_kali_mini_config
from OpenDEMON.kali.model.kali_model import KALIModel
from OpenDEMON.kali.architecture.cache import KVCache

@pytest.fixture
def mini_config():
    return get_kali_mini_config(device="cpu", dtype="float32")

@pytest.fixture
def model(mini_config):
    model = KALIModel(mini_config)
    model.load()
    return model

def test_parameter_count(model):
    params = model.count_parameters()
    assert params["total"] > 0
    assert params["trainable"] == params["total"]
    # We shouldn't claim it is intelligent
    assert "We do not claim KALI is intelligent until trained"

def test_forward_pass(model):
    batch_size = 2
    seq_len = 8
    input_ids = torch.randint(0, model.config.vocab_size, (batch_size, seq_len))
    
    with torch.no_grad():
        logits = model.transformer(input_ids)
        
    assert logits.shape == (batch_size, seq_len, model.config.vocab_size)

def test_loss_and_backprop(model):
    batch_size = 2
    seq_len = 8
    input_ids = torch.randint(0, model.config.vocab_size, (batch_size, seq_len))
    target_ids = torch.randint(0, model.config.vocab_size, (batch_size, seq_len))
    
    model.transformer.train()
    logits = model.transformer(input_ids)
    
    # Shift logits and labels for next token prediction
    shift_logits = logits[..., :-1, :].contiguous()
    shift_labels = target_ids[..., 1:].contiguous()
    
    loss_fct = torch.nn.CrossEntropyLoss()
    loss = loss_fct(shift_logits.view(-1, model.config.vocab_size), shift_labels.view(-1))
    
    assert loss.item() > 0
    
    # Backprop
    loss.backward()
    
    # Check if gradients exist
    has_grad = False
    for param in model.transformer.parameters():
        if param.grad is not None:
            has_grad = True
            break
            
    assert has_grad is True

def test_kv_cache(model):
    batch_size = 1
    
    # First pass
    input_ids = torch.tensor([[1, 2, 3]])
    kv_caches = [KVCache(batch_size, 1024, model.config.num_kv_heads, 
                         model.config.hidden_size // model.config.num_attention_heads,
                         device=model.config.device, dtype=torch.float32) 
                 for _ in range(model.config.num_layers)]
                 
    with torch.no_grad():
        logits1 = model.transformer(input_ids, kv_caches=kv_caches)
        
    assert kv_caches[0].current_seq_len == 3
    
    # Second pass (generation step)
    next_id = torch.tensor([[4]])
    with torch.no_grad():
        logits2 = model.transformer(next_id, kv_caches=kv_caches)
        
    assert kv_caches[0].current_seq_len == 4
    assert logits2.shape == (1, 1, model.config.vocab_size)

def test_save_load_pretrained(model):
    with tempfile.TemporaryDirectory() as tmpdir:
        model.save_pretrained(tmpdir)
        
        assert os.path.exists(os.path.join(tmpdir, "config.json"))
        assert os.path.exists(os.path.join(tmpdir, "pytorch_model.bin"))
        
        # Load it back
        loaded_model = KALIModel.from_pretrained(tmpdir, device="cpu", dtype="float32")
        
        assert loaded_model.health() is True
        assert loaded_model.config.hidden_size == model.config.hidden_size
        
        # Ensure weights match (test a random parameter)
        orig_weight = model.transformer.lm_head.weight.data
        loaded_weight = loaded_model.transformer.lm_head.weight.data
        
        assert torch.equal(orig_weight, loaded_weight)

def test_generation(model):
    # Testing that generate doesn't crash. (Output will be nonsense because it is untrained)
    output = model.generate("Hello", max_new_tokens=5)
    assert len(output) > 0
