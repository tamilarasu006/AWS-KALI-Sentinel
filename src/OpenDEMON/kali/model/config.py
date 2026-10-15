"""KALI AI Model Configuration."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class KALIModelConfig:
    """Configuration for a specific KALI AI model instance."""

    model_name: str
    model_path: str
    tokenizer_path: Optional[str] = None

    # Architecture dimensions
    context_length: int = 4096
    hidden_size: int = 4096
    num_layers: int = 32
    num_attention_heads: int = 32
    num_kv_heads: Optional[int] = None
    intermediate_size: int = 11008
    vocab_size: int = 32000

    # Execution parameters
    dtype: str = "float16"
    device: str = "cpu"

    def __post_init__(self):
        if self.num_kv_heads is None:
            self.num_kv_heads = self.num_attention_heads

def get_kali_mini_config(device="cpu", dtype="float32") -> KALIModelConfig:
    """Returns a KALI-Mini configuration optimized for local dev & testing."""
    return KALIModelConfig(
        model_name="KALI-Mini",
        model_path="./kali-mini",
        context_length=1024,
        hidden_size=256,
        num_layers=4,
        num_attention_heads=4,
        num_kv_heads=4,
        intermediate_size=1024,
        vocab_size=32000,
        device=device,
        dtype=dtype
    )
