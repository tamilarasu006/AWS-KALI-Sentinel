"""KALI AI Model Registry."""

from typing import Dict, List, Optional

from .model import KALIModelBase


class KALIModelRegistry:
    """Registry for managing KALI AI models."""

    def __init__(self):
        self._models: Dict[str, KALIModelBase] = {}
        self._default_model_name: Optional[str] = None

    def register_model(self, name: str, model: KALIModelBase, is_default: bool = False) -> None:
        """Register a model instance."""
        if name in self._models:
            raise ValueError(f"Model '{name}' is already registered.")
        self._models[name] = model
        if is_default or self._default_model_name is None:
            self._default_model_name = name

    def unregister_model(self, name: str) -> None:
        """Unregister a model instance."""
        if name not in self._models:
            raise KeyError(f"Model '{name}' not found in registry.")
        del self._models[name]
        if self._default_model_name == name:
            self._default_model_name = next(iter(self._models.keys())) if self._models else None

    def get_model(self, name: str) -> KALIModelBase:
        """Get a registered model by name."""
        if name not in self._models:
            raise KeyError(f"Model '{name}' not found in registry.")
        return self._models[name]

    def list_models(self) -> List[str]:
        """List all registered model names."""
        return list(self._models.keys())

    def default_model(self) -> Optional[KALIModelBase]:
        """Get the default registered model."""
        if self._default_model_name is None:
            return None
        return self._models[self._default_model_name]
