"""Key-Value Cache for autoregressive generation."""

import torch
from typing import Tuple, Optional

class KVCache:
    """A simple fixed-size key-value cache."""
    def __init__(self, batch_size: int, max_seq_len: int, num_kv_heads: int, head_dim: int, device: torch.device, dtype: torch.dtype):
        self.k_cache = torch.zeros(batch_size, num_kv_heads, max_seq_len, head_dim, device=device, dtype=dtype)
        self.v_cache = torch.zeros(batch_size, num_kv_heads, max_seq_len, head_dim, device=device, dtype=dtype)
        self.current_seq_len = 0

    def update(self, k: torch.Tensor, v: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Updates the cache with new keys and values.
        Args:
            k: (batch_size, num_kv_heads, seq_len, head_dim)
            v: (batch_size, num_kv_heads, seq_len, head_dim)
        Returns:
            The complete history of keys and values including the new ones.
        """
        seq_len = k.size(2)
        
        self.k_cache[:, :, self.current_seq_len : self.current_seq_len + seq_len, :] = k
        self.v_cache[:, :, self.current_seq_len : self.current_seq_len + seq_len, :] = v
        
        self.current_seq_len += seq_len
        
        return (
            self.k_cache[:, :, :self.current_seq_len, :],
            self.v_cache[:, :, :self.current_seq_len, :],
        )

    def reset(self):
        self.current_seq_len = 0
