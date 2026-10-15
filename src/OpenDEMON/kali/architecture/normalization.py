"""Root Mean Square Normalization (RMSNorm)."""

import torch
from torch import nn

class RMSNorm(nn.Module):
    """RMSNorm implementation for transformer block normalization."""

    def __init__(self, dim: int, eps: float = 1e-5):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def _norm(self, x: torch.Tensor) -> torch.Tensor:
        """Calculate RMS norm."""
        return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply RMS norm to input tensor.
        
        Args:
            x (torch.Tensor): Input tensor of shape (..., dim)
            
        Returns:
            torch.Tensor: Normalized tensor with same shape as input
        """
        output = self._norm(x.float()).type_as(x)
        return output * self.weight
