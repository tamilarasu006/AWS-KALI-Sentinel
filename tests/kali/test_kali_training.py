import pytest
import os
import tempfile
import torch
from OpenDEMON.kali.model.config import get_kali_mini_config
from OpenDEMON.kali.model.kali_model import KALIModel
from OpenDEMON.kali.tokenizer.bpe_tokenizer import KALIBPETokenizer
from OpenDEMON.kali.training.pipeline import KALITrainingPipeline
from OpenDEMON.kali.training.data import DataPipeline

@pytest.fixture
def mini_model():
    config = get_kali_mini_config(device="cpu", dtype="float32")
    model = KALIModel(config)
    model.load()
    # Mock real tokenizer for test
    model.tokenizer = KALIBPETokenizer(vocab_size=32000)
    # Give it dummy merges so encode doesn't crash on any string
    return model

@pytest.fixture
def tokenizer(mini_model):
    return mini_model.tokenizer

def test_data_pipeline_scrubbing(tokenizer):
    dp = DataPipeline(tokenizer)
    raw = [
        "Normal text without secrets.",
        "Here is my api_key: 'sk-1234567890abcdef1234567890abcdef'",
        "Another string",
        "Normal text without secrets." # Duplicate
    ]
    
    cleaned = dp.clean(raw)
    assert len(cleaned) == 3
    assert "api_key" not in cleaned[1] # It was removed
    
    deduped = dp.deduplicate(cleaned)
    assert len(deduped) == 2

def test_e2e_training_pipeline(mini_model, tokenizer):
    pipeline = KALITrainingPipeline(mini_model, tokenizer)
    
    dummy_data = [
        "This is a pretraining corpus sentence 1.",
        "This is a pretraining corpus sentence 2.",
        "The quick brown fox jumps over the lazy dog."
    ]
    
    # Run pretraining
    pipeline.run_pretraining(dummy_data, epochs=1, batch_size=2)
    
    # Run SFT
    pipeline.run_instruction_finetuning(["User: Hello\nAssistant: Hi!"], epochs=1, batch_size=1)
    
    # Checkpoint
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline.trainer.save_checkpoint(tmpdir)
        assert os.path.exists(os.path.join(tmpdir, "optimizer.pt"))
        assert os.path.exists(os.path.join(tmpdir, "pytorch_model.bin"))
        
        # Test Resume
        pipeline.trainer.resume_from_checkpoint(tmpdir)
        assert pipeline.trainer.current_epoch == 2
