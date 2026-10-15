import pytest
import torch
import torch.nn as nn
from unittest.mock import MagicMock, patch
from OpenDEMON.kali.finetuning.config import FinetuneConfig
from OpenDEMON.kali.finetuning.lora import LoRAFinetuner
from OpenDEMON.kali.finetuning.instruction import InstructionDataset

# A tiny mock model
class TinyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.q_proj = nn.Linear(10, 10)
        self.v_proj = nn.Linear(10, 10)
        
    def forward(self, input_ids=None, labels=None, **kwargs):
        x = self.q_proj(torch.randn(1, 10))
        loss = x.sum()
        return MagicMock(loss=loss)
        
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        return cls()

@patch("OpenDEMON.kali.finetuning.lora.get_peft_model")
@patch("OpenDEMON.kali.finetuning.lora.LoraConfig")
def test_lora_finetuner(mock_lora_config, mock_get_peft_model):
    config = FinetuneConfig(rank=4, alpha=8, target_modules=["q_proj"])
    tuner = LoRAFinetuner(config)
    
    # Mocking PEFT behavior
    mock_peft_model = MagicMock()
    mock_peft_model.return_value = MagicMock(loss=torch.tensor(0.5, requires_grad=True))
    mock_peft_model.merge_and_unload.return_value = TinyModel()
    mock_get_peft_model.return_value = mock_peft_model
    
    # Test loading
    tuner.load_base_model(TinyModel, "dummy/path")
    assert tuner.base_model is not None
    
    # Test preparing adapter
    tuner.prepare_adapter()
    assert tuner.model is not None
    mock_get_peft_model.assert_called_once()
    
    # Test train step
    optimizer = MagicMock()
    batch = {"input_ids": torch.tensor([[1, 2, 3]])}
    loss = tuner.train_step(batch, optimizer)
    assert loss == 0.125
    
    # Test merge
    tuner.merge_adapter()
    assert tuner.model == tuner.base_model

def test_instruction_dataset():
    tokenizer = MagicMock()
    tokenizer.eos_token = "<eos>"
    tokenizer.return_value = {
        "input_ids": [torch.tensor([1, 2, 3, 4, 5])],
        "attention_mask": [torch.tensor([1, 1, 1, 1, 1])]
    }
    
    data = [{"instruction": "Do this", "input": "", "output": "Done"}]
    dataset = InstructionDataset(data, tokenizer, max_length=5)
    
    assert len(dataset) == 1
    item = dataset[0]
    assert "input_ids" in item
    assert "labels" in item
    assert "attention_mask" in item
