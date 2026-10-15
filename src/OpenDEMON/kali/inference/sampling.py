"""Sampling functions for KALI AI."""

import torch
from typing import Optional, List

def sample_token(
    logits: torch.Tensor,
    temperature: float = 1.0,
    top_k: int = 0,
    top_p: float = 1.0,
    repetition_penalty: float = 1.0,
    previous_tokens: Optional[List[int]] = None,
    seed: Optional[int] = None,
) -> int:
    """
    Samples a single token from logits.
    
    Args:
        logits: (vocab_size,) tensor of logits for the next token.
        temperature: Controls randomness (0.0 = deterministic argmax).
        top_k: Keep only top K tokens (0 = no filtering).
        top_p: Nucleus filtering (1.0 = no filtering).
        repetition_penalty: Penalty for previously generated tokens (1.0 = no penalty).
        previous_tokens: List of previously generated token IDs.
        seed: Random seed for deterministic generation if temperature > 0.
        
    Returns:
        int: The selected token ID.
    """
    if seed is not None:
        torch.manual_seed(seed)

    # Apply repetition penalty
    if repetition_penalty != 1.0 and previous_tokens:
        for token_id in set(previous_tokens):
            if logits[token_id] < 0:
                logits[token_id] *= repetition_penalty
            else:
                logits[token_id] /= repetition_penalty

    # Deterministic fallback
    if temperature == 0.0:
        return int(torch.argmax(logits).item())

    # Apply temperature
    logits = logits / temperature

    # Apply top_k
    if top_k > 0:
        v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
        logits[logits < v[-1]] = float('-inf')

    # Apply top_p (nucleus)
    if top_p < 1.0:
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)

        # Remove tokens with cumulative probability above the threshold
        sorted_indices_to_remove = cumulative_probs > top_p
        # Shift the indices to the right to keep also the first token above the threshold
        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
        sorted_indices_to_remove[..., 0] = 0

        indices_to_remove = sorted_indices[sorted_indices_to_remove]
        logits[indices_to_remove] = float('-inf')

    probs = torch.softmax(logits, dim=-1)
    next_token = torch.multinomial(probs, num_samples=1)
    
    return int(next_token.item())
