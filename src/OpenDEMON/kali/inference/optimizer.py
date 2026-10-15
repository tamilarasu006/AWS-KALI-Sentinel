import torch
from dataclasses import dataclass
from typing import Optional

@dataclass
class InferenceProfile:
    name: str
    dtype: torch.dtype
    max_batch_size: int
    max_context: int
    quantization_mode: str
    attention_implementation: str

def get_inference_profile(name: str) -> InferenceProfile:
    """
    Returns configurable inference profiles depending on hardware availability.
    Safely falls back from GPU requirements.
    """
    has_cuda = torch.cuda.is_available()
    
    if name == "development":
        return InferenceProfile(
            name="development",
            dtype=torch.float32,
            max_batch_size=1,
            max_context=512,
            quantization_mode="none",
            attention_implementation="math"
        )
    elif name == "balanced":
        return InferenceProfile(
            name="balanced",
            dtype=torch.bfloat16 if has_cuda and torch.cuda.is_bf16_supported() else torch.float32,
            max_batch_size=4,
            max_context=1024,
            quantization_mode="none",
            attention_implementation="sdpa" if hasattr(torch.nn.functional, "scaled_dot_product_attention") else "math"
        )
    elif name == "performance":
        return InferenceProfile(
            name="performance",
            dtype=torch.float16 if has_cuda else torch.float32,
            max_batch_size=16,
            max_context=2048,
            quantization_mode="none",
            attention_implementation="sdpa" if hasattr(torch.nn.functional, "scaled_dot_product_attention") else "math"
        )
    elif name == "low_memory":
        return InferenceProfile(
            name="low_memory",
            dtype=torch.float32,
            max_batch_size=1,
            max_context=512,
            quantization_mode="int8",
            attention_implementation="math"
        )
    
    # Default safe fallback
    return InferenceProfile(
        name="default",
        dtype=torch.float32,
        max_batch_size=1,
        max_context=1024,
        quantization_mode="none",
        attention_implementation="math"
    )
