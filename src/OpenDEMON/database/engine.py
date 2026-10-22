import os
import ssl
from typing import Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine


def _build_engine() -> AsyncEngine:
    """Build the SQLAlchemy async engine, reading config at call time (not import time)."""
    # Re-read from database/config to pick up DATABASE_URL that may have been set
    # after this module was imported (e.g., loaded from .env by the CLI entry point).
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://demon:development_password@localhost:5432/demon_ai"
    )
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    pool_size = int(os.environ.get("DB_POOL_SIZE", "10"))
    max_overflow = int(os.environ.get("DB_MAX_OVERFLOW", "20"))
    pool_timeout = int(os.environ.get("DB_POOL_TIMEOUT", "30"))
    pool_recycle = int(os.environ.get("DB_POOL_RECYCLE", "1800"))

    _is_pooler = "pooler.supabase.com" in url
    host_candidate = url.split("@")[-1].split(":")[0].split("/")[0] if "@" in url else "localhost"
    _sni_host = os.environ.get("SUPABASE_POOLER_SNI", host_candidate)
    _is_ip_url = not any(c.isalpha() for c in host_candidate)

    _connect_args: dict[str, Any] = {}
    if _is_pooler or _is_ip_url:
        _ssl_ctx = ssl.create_default_context()
        _ssl_ctx.check_hostname = False
        _ssl_ctx.verify_mode = ssl.CERT_NONE
        _connect_args = {
            "ssl": _ssl_ctx,
            "statement_cache_size": 0,
        }
        if _is_ip_url:
            _connect_args["server_settings"] = {"sni": _sni_host}

    return create_async_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=True,
        connect_args=_connect_args,
    )


class _LazyEngine:
    """Proxy that defers SQLAlchemy engine creation until first attribute access."""
    _engine: AsyncEngine | None = None
    _session_factory: Any = None

    def _get_engine(self) -> AsyncEngine:
        if self._engine is None:
            _LazyEngine._engine = _build_engine()
            _LazyEngine._session_factory = async_sessionmaker(
                bind=_LazyEngine._engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )
        return self._engine  # type: ignore[return-value]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_engine(), name)

    # AsyncEngine-specific dunder methods used by SQLAlchemy
    async def connect(self):
        return await self._get_engine().connect()

    async def begin(self):
        return await self._get_engine().begin()

    async def dispose(self, **kwargs):
        if self._engine:
            return await self._engine.dispose(**kwargs)

    @property
    def url(self):
        return self._get_engine().url

    @property
    def dialect(self):
        return self._get_engine().dialect

    @property
    def pool(self):
        return self._get_engine().pool

    @property
    def sync_engine(self):
        return self._get_engine().sync_engine

    @property
    def echo(self):
        return self._get_engine().echo


_lazy = _LazyEngine()

# Public names that the rest of the codebase imports
engine: AsyncEngine = _lazy  # type: ignore[assignment]


class _LazySessionMaker:
    """Proxy to async_sessionmaker that defers creation until first call."""

    def __call__(self, **kwargs) -> AsyncSession:
        _lazy._get_engine()  # ensure engine + session factory are built
        return _LazyEngine._session_factory(**kwargs)  # type: ignore[misc]

    def __getattr__(self, name: str) -> Any:
        _lazy._get_engine()
        return getattr(_LazyEngine._session_factory, name)


AsyncSessionLocal = _LazySessionMaker()  # type: ignore[assignment]
