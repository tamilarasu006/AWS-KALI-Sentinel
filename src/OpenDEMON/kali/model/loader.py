"""KALI Model loader."""

from .config import KALIModelConfig
from .kali_model import KALIModel


def load_model(config: KALIModelConfig) -> KALIModel:
    """Instantiate and load a KALIModel from config."""
    model = KALIModel(config)
    model.load()
    return model
