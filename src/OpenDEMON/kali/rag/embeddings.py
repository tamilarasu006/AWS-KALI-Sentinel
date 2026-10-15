from abc import ABC, abstractmethod
from typing import List
import random

class EmbeddingProvider(ABC):
    """Abstract interface for generating vector embeddings."""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Embed a single string."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of strings."""
        pass

class FakeEmbeddingProvider(EmbeddingProvider):
    """Generates random embeddings for testing purposes."""

    def __init__(self, dimension: int = 768):
        self.dimension = dimension

    def embed(self, text: str) -> List[float]:
        random.seed(hash(text))
        return [random.uniform(-1, 1) for _ in range(self.dimension)]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(text) for text in texts]
