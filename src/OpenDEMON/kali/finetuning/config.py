from dataclasses import dataclass, field
from typing import List

@dataclass
class KALISFTConfig:
    learning_rate: float = 2e-4
    batch_size: int = 4
    gradient_accumulation: int = 4
    epochs: int = 3
    warmup: float = 0.1
    scheduler: str = "cosine"
    weight_decay: float = 0.01
    max_sequence_length: int = 512
    gradient_clipping: float = 1.0
    checkpoint_interval: int = 100
    evaluation_interval: int = 100
    seed: int = 42
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj"])
    rank: int = 8
    alpha: int = 16
    dropout: float = 0.05
