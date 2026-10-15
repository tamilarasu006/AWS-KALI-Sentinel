"""Token Embedding module."""

import torch
from torch import nn

class TokenEmbedding(nn.Module):
    """Vocabulary token embedding."""
    
    def __init__(self, vocab_size: int, hidden_size: int):
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.weight = nn.Parameter(torch.empty((vocab_size, hidden_size)))
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.normal_(self.weight, mean=0.0, std=self.hidden_size ** -0.5)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        """
        Args:
            input_ids: Tensor of shape (batch_size, seq_len)
        Returns:
            Tensor of shape (batch_size, seq_len, hidden_size)
        """
        import torch.nn.functional as F
        return F.embedding(input_ids, self.weight)
