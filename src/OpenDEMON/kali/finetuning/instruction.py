import torch
from torch.utils.data import Dataset
from typing import List, Dict, Any
from .lora import LoRAFinetuner

class InstructionDataset(Dataset):
    """Formats raw instruction data for causal language modeling."""
    
    def __init__(self, data: List[Dict[str, str]], tokenizer: Any, max_length: int = 512):
        """
        data expected format: [{"instruction": "...", "input": "...", "output": "..."}]
        """
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.prompt_template = (
            "Below is an instruction that describes a task, paired with an input that provides further context. "
            "Write a response that appropriately completes the request.\n\n"
            "### Instruction:\n{instruction}\n\n### Input:\n{input}\n\n### Response:\n"
        )

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = self.data[idx]
        
        instruction = item.get("instruction", "")
        input_text = item.get("input", "")
        output = item.get("output", "")
        
        prompt = self.prompt_template.format(instruction=instruction, input=input_text)
        full_text = prompt + output + self.tokenizer.eos_token
        
        tokens = self.tokenizer(
            full_text, 
            truncation=True, 
            max_length=self.max_length, 
            padding="max_length",
            return_tensors="pt"
        )
        
        input_ids = tokens["input_ids"][0]
        attention_mask = tokens["attention_mask"][0]
        
        # Mask prompt out in labels so we only train on output
        prompt_len = len(self.tokenizer(prompt)["input_ids"])
        labels = input_ids.clone()
        labels[:prompt_len] = -100 # PyTorch ignore_index
        labels[attention_mask == 0] = -100
        
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels
        }


class InstructionFinetuner:
    """Wrapper that combines an InstructionDataset with a LoRAFinetuner."""
    
    def __init__(self, tuner: LoRAFinetuner, tokenizer: Any):
        self.tuner = tuner
        self.tokenizer = tokenizer
        
    def train(self, dataset: InstructionDataset, epochs: int):
        # Implementation of full training loop specific to instruction tuning
        # In a real scenario, this would use Trainer/accelerator
        pass
