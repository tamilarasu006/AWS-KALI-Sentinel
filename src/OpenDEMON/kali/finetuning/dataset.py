import torch
from torch.utils.data import Dataset
from typing import List, Dict, Any
import json
from .chat_template import KALIChatTemplate

class SFTDataset(Dataset):
    def __init__(self, data: List[Dict[str, Any]], chat_template: KALIChatTemplate, max_length: int = 512):
        self.data = self._normalize(data)
        self.chat_template = chat_template
        self.max_length = max_length
        
    def _normalize(self, raw_data: List[Dict[str, Any]]) -> List[List[Dict[str, str]]]:
        normalized = []
        for item in raw_data:
            if "messages" in item:
                normalized.append(item["messages"])
            elif "instruction" in item and "output" in item:
                msgs = [{"role": "user", "content": item["instruction"]}]
                if item.get("input"): msgs[0]["content"] += f"\n{item['input']}"
                msgs.append({"role": "assistant", "content": item["output"]})
                normalized.append(msgs)
        return normalized

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        messages = self.data[idx]
        
        # very simple tokenization & masking for the baseline model (character level)
        # We need a proper masking logic, but for dummy tokenizers we just find index of assistant responses
        # Here we just encode everything and mask -100 for non-assistant
        
        input_ids = []
        labels = []
        
        for msg in messages:
            role = msg["role"].upper()
            text = f"<{role}>\n{msg['content']}\n\n"
            tokens = self.chat_template.tokenizer.encode(text, add_bos=False)
            input_ids.extend(tokens)
            
            if role == "ASSISTANT":
                labels.extend(tokens)
            else:
                labels.extend([-100] * len(tokens))
                
        # pad/truncate
        input_ids = input_ids[:self.max_length]
        labels = labels[:self.max_length]
        
        att_mask = [1] * len(input_ids)
        
        # pad
        pad_id = self.chat_template.tokenizer.special_tokens.pad_token_id
        while len(input_ids) < self.max_length:
            input_ids.append(pad_id)
            labels.append(-100)
            att_mask.append(0)
            
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(att_mask, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long)
        }
