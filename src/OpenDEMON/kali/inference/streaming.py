"""Streaming generation for KALI AI."""

import torch
from typing import List, Optional, Any, Iterator
from OpenDEMON.kali.architecture.transformer import KALITransformer
from OpenDEMON.kali.architecture.cache import KVCache
from OpenDEMON.kali.inference.sampling import sample_token

def stream_text(
    model: KALITransformer,
    prompt: str,
    tokenizer: Any,
    max_new_tokens: int = 50,
    temperature: float = 1.0,
    top_k: int = 0,
    top_p: float = 1.0,
    repetition_penalty: float = 1.0,
    stop_tokens: Optional[List[str]] = None,
    seed: Optional[int] = None,
) -> Iterator[str]:
    """
    Generates text autoregressively and yields it token-by-token.
    
    Args:
        model: The KALITransformer instance.
        prompt: The input prompt string.
        tokenizer: An object with `.encode(text) -> List[int]` and `.decode(List[int]) -> str`.
        max_new_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature.
        top_k: Top-k sampling limit.
        top_p: Nucleus sampling probability.
        repetition_penalty: Repetition penalty factor.
        stop_tokens: List of strings that will stop generation when emitted.
        seed: Random seed for deterministic generation.
        
    Yields:
        String representing the newly generated token.
    """
    input_ids = tokenizer.encode(prompt)
    if not input_ids:
        return
        
    device = next(model.parameters()).device
    dtype = next(model.parameters()).dtype
    
    input_tensor = torch.tensor([input_ids], device=device)
    
    batch_size = 1
    head_dim = model.config.hidden_size // model.config.num_attention_heads
    
    kv_caches = [
        KVCache(
            batch_size=batch_size,
            max_seq_len=model.config.context_length,
            num_kv_heads=model.config.num_kv_heads,
            head_dim=head_dim,
            device=device,
            dtype=dtype,
        )
        for _ in range(model.config.num_layers)
    ]
    
    generated_tokens = []
    current_input = input_tensor
    
    for _ in range(max_new_tokens):
        with torch.no_grad():
            logits = model(current_input, kv_caches=kv_caches)
            
        next_token_logits = logits[0, -1, :]
        
        next_token_id = sample_token(
            logits=next_token_logits,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            previous_tokens=generated_tokens,
            seed=seed,
        )
        
        generated_tokens.append(next_token_id)
        current_input = torch.tensor([[next_token_id]], device=device)
        
        # We decode the single token to string
        # In a real subword tokenizer, partial decodes can be tricky, 
        # but for a simple tokenizer decoding the last token works.
        yield tokenizer.decode([next_token_id])
        
        # Check for stop tokens if provided
        if stop_tokens:
            current_text = tokenizer.decode(generated_tokens)
            if any(current_text.endswith(stop) for stop in stop_tokens):
                break
