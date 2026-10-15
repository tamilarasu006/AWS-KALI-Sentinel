"""KALI Model abstractions."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator

from .config import KALIModelConfig


class KALIModelBase(ABC):
    """Abstract base class for KALI AI models."""

    def __init__(self, config: KALIModelConfig):
        self.config = config

    @abstractmethod
    def load(self) -> None:
        """Load the model weights into memory."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unload the model weights from memory."""
        pass

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a complete completion for the given prompt."""
        pass

    @abstractmethod
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Stream the completion for the given prompt."""
        pass

    @abstractmethod
    def health(self) -> bool:
        """Check the health status of the model."""
        pass

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return model metadata."""
        pass
