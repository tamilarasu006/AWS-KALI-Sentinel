"""SwiGLU Multi-Layer Perceptron."""

import torch
from torch import nn
import torch.nn.functional as F

class SwiGLU(nn.Module):
    """SwiGLU activation based MLP."""
    def __init__(self, hidden_size: int, intermediate_size: int):
        super().__init__()
        self.gate_proj = nn.Linear(hidden_size, intermediate_size, bias=False)
        self.up_proj = nn.Linear(hidden_size, intermediate_size, bias=False)
        self.down_proj = nn.Linear(intermediate_size, hidden_size, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Tensor of shape (..., hidden_size)
        Returns:
            Tensor of shape (..., hidden_size)
        """
        return self.down_proj(F.silu(self.gate_proj(x)) * self.up_proj(x))
