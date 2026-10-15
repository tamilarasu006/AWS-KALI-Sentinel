import re
import hashlib
from typing import List, Dict, Any, Tuple
import torch
from torch.utils.data import Dataset, DataLoader
from OpenDEMON.kali.tokenizer.bpe_tokenizer import KALIBPETokenizer

class KALIDataset(Dataset):
    """PyTorch Dataset for KALI."""
    def __init__(self, data: List[Dict[str, Any]], tokenizer: KALIBPETokenizer, context_length: int = 1024):
        self.data = data
        self.tokenizer = tokenizer
        self.context_length = context_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # We assume the packing is done prior, this just returns the tensors
        item = self.data[idx]
        return {
            "input_ids": torch.tensor(item["input_ids"], dtype=torch.long),
            "labels": torch.tensor(item["labels"], dtype=torch.long)
        }

class DataPipeline:
    """End-to-End Data Preparation Pipeline for KALI Training."""
    
    def __init__(self, tokenizer: KALIBPETokenizer, context_length: int = 1024):
        self.tokenizer = tokenizer
        self.context_length = context_length
        # Simplistic regex to catch basic API keys or secrets (for demonstration purposes)
        self.secret_pattern = re.compile(r'(?i)(api_key|secret|password|token)\s*[:=]\s*["\'][a-zA-Z0-9_-]{16,}["\']')

    def load_raw_data(self, source: List[str]) -> List[str]:
        """Loads data from source list."""
        return source

    def clean(self, data: List[str]) -> List[str]:
        """Scrub secrets and perform basic cleaning."""
        cleaned = []
        for text in data:
            if self.secret_pattern.search(text):
                # Filter out strings with secrets entirely
                continue
            cleaned.append(text.strip())
        return cleaned

    def deduplicate(self, data: List[str]) -> List[str]:
        """Remove exact duplicates via hashing."""
        seen = set()
        deduped = []
        for text in data:
            h = hashlib.sha256(text.encode('utf-8')).hexdigest()
            if h not in seen:
                seen.add(h)
                deduped.append(text)
        return deduped

    def filter_quality(self, data: List[str], min_length: int = 10) -> List[str]:
        """Filter out low-quality/too short snippets."""
        return [t for t in data if len(t) >= min_length]

    def tokenize_and_pack(self, data: List[str], is_sft: bool = False) -> List[Dict[str, Any]]:
        """
        Tokenize text and pack into context-length chunks.
        For SFT, we apply chat templates or masking to user inputs in labels.
        """
        packed_data = []
        current_chunk = []
        
        for text in data:
            # We add bos manually or assume it's in the text
            tokens = self.tokenizer.encode(text, add_bos=True)
            tokens.append(self.tokenizer.special_tokens.eos_token_id)
            
            if is_sft:
                # Naive SFT logic: just train on the whole thing for now, 
                # but ideally we mask the user prompt in the labels.
                pass
                
            current_chunk.extend(tokens)
            
            while len(current_chunk) >= self.context_length:
                chunk = current_chunk[:self.context_length]
                packed_data.append({
                    "input_ids": chunk,
                    "labels": chunk.copy()  # For causal LM, labels are just shifted during loss calc
                })
                current_chunk = current_chunk[self.context_length:]
                
        # Handle remainder if we want to pad it (skipping for simplicity if it's too short)
        if len(current_chunk) > 10: # arbitrary minimum
            pad_len = self.context_length - len(current_chunk)
            chunk = current_chunk + [self.tokenizer.special_tokens.pad_token_id] * pad_len
            packed_data.append({
                "input_ids": chunk,
                "labels": chunk.copy()
            })
            
        return packed_data

    def prepare_dataloader(self, data: List[str], batch_size: int = 4, is_sft: bool = False) -> DataLoader:
        """Runs the full prep pipeline."""
        d1 = self.clean(data)
        d2 = self.deduplicate(d1)
        d3 = self.filter_quality(d2)
        packed = self.tokenize_and_pack(d3, is_sft)
        
        dataset = KALIDataset(packed, self.tokenizer, self.context_length)
        return DataLoader(dataset, batch_size=batch_size, shuffle=True)
