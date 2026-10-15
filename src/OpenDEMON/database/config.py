import os
from pydantic import BaseModel, Field

class DatabaseConfig(BaseModel):
    url: str = Field(
        default_factory=lambda: os.environ.get(
            "DATABASE_URL", 
            "postgresql+asyncpg://demon:development_password@localhost:5432/demon_ai"
        )
    )
    pool_size: int = Field(default_factory=lambda: int(os.environ.get("DB_POOL_SIZE", "10")))
    max_overflow: int = Field(default_factory=lambda: int(os.environ.get("DB_MAX_OVERFLOW", "20")))
    pool_timeout: int = Field(default_factory=lambda: int(os.environ.get("DB_POOL_TIMEOUT", "30")))
    pool_recycle: int = Field(default_factory=lambda: int(os.environ.get("DB_POOL_RECYCLE", "1800")))
    pool_pre_ping: bool = True

def _make_db_config() -> DatabaseConfig:
    return DatabaseConfig()

# Lazy singleton: evaluated on first access, not at import time.
# This ensures DATABASE_URL from .env is already in os.environ.
class _LazyDbConfig:
    _instance: "DatabaseConfig | None" = None

    def __getattr__(self, name: str):
        if self._instance is None:
            _LazyDbConfig._instance = DatabaseConfig()
        return getattr(self._instance, name)

db_config = _LazyDbConfig()  # type: ignore[assignment]
