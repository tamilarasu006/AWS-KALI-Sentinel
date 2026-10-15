"""KALI AI Transformer Architecture."""

import torch
from torch import nn
from typing import Optional, List, Tuple
import math

from OpenDEMON.kali.model.config import KALIModelConfig
from OpenDEMON.kali.architecture.normalization import RMSNorm
from OpenDEMON.kali.architecture.rotary import RotaryEmbedding
from OpenDEMON.kali.architecture.embeddings import TokenEmbedding
from OpenDEMON.kali.architecture.mlp import SwiGLU
from OpenDEMON.kali.architecture.attention import CausalSelfAttention
from OpenDEMON.kali.architecture.cache import KVCache

class TransformerBlock(nn.Module):
    """A single Transformer block."""
    def __init__(self, config: KALIModelConfig):
        super().__init__()
        self.hidden_size = config.hidden_size
        self.input_layernorm = RMSNorm(config.hidden_size)
        self.self_attn = CausalSelfAttention(
            hidden_size=config.hidden_size,
            num_attention_heads=config.num_attention_heads,
            num_kv_heads=config.num_kv_heads,
        )
        self.post_attention_layernorm = RMSNorm(config.hidden_size)
        self.mlp = SwiGLU(
            hidden_size=config.hidden_size,
            intermediate_size=config.intermediate_size,
        )

    def forward(
        self,
        hidden_states: torch.Tensor,
        cos: torch.Tensor,
        sin: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        kv_cache: Optional[KVCache] = None,
    ) -> torch.Tensor:
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        hidden_states = self.self_attn(
            hidden_states=hidden_states,
            cos=cos,
            sin=sin,
            attention_mask=attention_mask,
            kv_cache=kv_cache,
        )
        hidden_states = residual + hidden_states

        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = residual + hidden_states

        return hidden_states

class KALITransformer(nn.Module):
    """The complete KALI AI decoder-only transformer model."""
    def __init__(self, config: KALIModelConfig):
        super().__init__()
        self.config = config
        self.vocab_size = config.vocab_size
        
        # Token Embeddings
        self.embed_tokens = TokenEmbedding(config.vocab_size, config.hidden_size)
        
        # Transformer Blocks
        self.layers = nn.ModuleList([TransformerBlock(config) for _ in range(config.num_layers)])
        
        # Final Norm
        self.norm = RMSNorm(config.hidden_size)
        
        # Rotary Embeddings
        head_dim = config.hidden_size // config.num_attention_heads
        self.rotary_emb = RotaryEmbedding(
            dim=head_dim,
            max_position_embeddings=config.context_length,
        )
        
        # LM Head
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

    def _prepare_decoder_attention_mask(self, batch_size, seq_length, dtype, device, past_key_values_length=0):
        # Create causal mask
        mask = torch.full((seq_length, seq_length), torch.finfo(dtype).min, device=device)
        mask_cond = torch.arange(mask.size(-1), device=device)
        mask.masked_fill_(mask_cond < (mask_cond + 1).view(mask.size(-1), 1), 0)
        
        if past_key_values_length > 0:
            mask = torch.cat([torch.zeros(seq_length, past_key_values_length, dtype=dtype, device=device), mask], dim=-1)
            
        return mask[None, None, :, :].expand(batch_size, 1, seq_length, seq_length + past_key_values_length)

    def forward(
        self,
        input_ids: torch.Tensor,
        kv_caches: Optional[List[KVCache]] = None,
    ) -> torch.Tensor:
        """
        Forward pass of the model.
        Args:
            input_ids: (batch_size, seq_len)
            kv_caches: list of KVCache objects, one per layer
        Returns:
            logits: (batch_size, seq_len, vocab_size)
        """
        batch_size, seq_len = input_ids.shape
        
        past_key_values_length = 0
        if kv_caches is not None and kv_caches[0].current_seq_len > 0:
            past_key_values_length = kv_caches[0].current_seq_len

        hidden_states = self.embed_tokens(input_ids)
        
        # Get RoPE
        # We need RoPE for the full sequence length (past + current)
        cos, sin = self.rotary_emb(hidden_states, seq_len=seq_len + past_key_values_length)
        # Slicing the RoPE for the current seq_len
        cos = cos[None, None, past_key_values_length : past_key_values_length + seq_len, :]
        sin = sin[None, None, past_key_values_length : past_key_values_length + seq_len, :]

        # Attention mask
        attention_mask = None
        if seq_len > 1:
            attention_mask = self._prepare_decoder_attention_mask(
                batch_size, seq_len, hidden_states.dtype, hidden_states.device, past_key_values_length
            )

        # Pass through transformer blocks
        for idx, layer in enumerate(self.layers):
            kv_cache = kv_caches[idx] if kv_caches is not None else None
            hidden_states = layer(
                hidden_states,
                cos=cos,
                sin=sin,
                attention_mask=attention_mask,
                kv_cache=kv_cache,
            )

        hidden_states = self.norm(hidden_states)
        logits = self.lm_head(hidden_states)

        return logits
