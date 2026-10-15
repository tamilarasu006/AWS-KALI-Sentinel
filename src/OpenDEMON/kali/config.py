"""KALI AI Configuration."""

import os
from dataclasses import dataclass, field


@dataclass
class KALIConfig:
    """Global configuration for KALI AI."""

    config_dir: str = field(default_factory=lambda: os.environ.get("KALI_CONFIG_DIR", "~/.kali"))
    models_dir: str = field(default_factory=lambda: os.environ.get("KALI_MODELS_DIR", "~/.kali/models"))
    default_device: str = field(default_factory=lambda: os.environ.get("KALI_DEFAULT_DEVICE", "cpu"))

    @classmethod
    def from_env(cls) -> "KALIConfig":
        """Load configuration from environment variables."""
        return cls()
