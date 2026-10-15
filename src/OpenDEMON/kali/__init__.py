"""KALI AI Foundation."""

from .config import KALIConfig
from .registry import KALIModelRegistry

_global_registry = KALIModelRegistry()

def get_registry() -> KALIModelRegistry:
    return _global_registry

__all__ = ["KALIConfig", "KALIModelRegistry", "get_registry"]
