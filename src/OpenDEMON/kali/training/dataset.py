import torch
from torch.utils.data import Dataset
from typing import List, Dict, Any

class KALIDataset(Dataset):
    """
    PyTorch Dataset for KALI training.
    Expects pre-tokenized and packed input IDs.
    """
    def __init__(self, data: List[List[int]]):
        self.data = data

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        input_ids = torch.tensor(self.data[idx], dtype=torch.long)
        
        # Shift inputs for causal language modeling labels
        labels = input_ids.clone()
        
        return {
            "input_ids": input_ids,
            "labels": labels
        }
