"""Database session management and connectivity for KALI Sentinel.

Supports PostgreSQL + pgvector, Supabase poolers, SQLite (for testing),
and safe fallback when the database is unavailable during local development.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import os
import ssl
from typing import Any, AsyncIterator, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)

# Global singletons
_ENGINE: Optional[AsyncEngine] = None
_SESSION_FACTORY: Optional[async_sessionmaker[AsyncSession]] = None


def get_database_url() -> str:
    """Retrieve the normalized asynchronous database URL from environment."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return ""

    # Normalize standard postgresql:// to postgresql+asyncpg://
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    elif url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]

    return url


def is_database_configured() -> bool:
    """Check if a valid database URL is configured in the environment."""
    return bool(get_database_url())


def is_database_required() -> bool:
    """Check if database persistence is strictly required (raises errors on failure)."""
    raw = os.getenv("SENTINEL_DB_REQUIRED", "false").lower()
    return raw in ("1", "true", "yes", "on")


def _build_engine(database_url: str) -> AsyncEngine:
    """Construct an async SQLAlchemy engine with proper pool and SSL settings."""
    connect_args: Dict[str, Any] = {}

    if "sqlite" in database_url:
        return create_async_engine(
            database_url,
            connect_args={"check_same_thread": False},
        )

    # Supabase pooler or external SSL support
    is_pooler = "pooler.supabase.com" in database_url or "supabase" in database_url
    if is_pooler or os.getenv("DB_SSL", "true").lower() in ("1", "true", "yes"):
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_ctx
        connect_args["statement_cache_size"] = 0

    pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "10"))
    pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))

    return create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


def get_engine() -> Optional[AsyncEngine]:
    """Get or initialize the shared AsyncEngine."""
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is not None:
        return _ENGINE

    url = get_database_url()
    if not url:
        return None

    try:
        _ENGINE = _build_engine(url)
        _SESSION_FACTORY = async_sessionmaker(
            bind=_ENGINE,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        logger.info("Initialized KALI Sentinel database engine.")
        return _ENGINE
    except Exception as exc:
        logger.warning("Failed to initialize database engine: %s", exc)
        return None


def get_session_factory() -> Optional[async_sessionmaker[AsyncSession]]:
    """Get the async session factory if database is configured."""
    global _SESSION_FACTORY
    if _SESSION_FACTORY is not None:
        return _SESSION_FACTORY
    get_engine()
    return _SESSION_FACTORY


def set_engine_for_testing(engine: Optional[AsyncEngine]) -> None:
    """Override engine for pytest fixtures (e.g. in-memory SQLite)."""
    global _ENGINE, _SESSION_FACTORY
    _ENGINE = engine
    if engine is not None:
        _SESSION_FACTORY = async_sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    else:
        _SESSION_FACTORY = None


@asynccontextmanager
async def get_db_session() -> AsyncIterator[Optional[AsyncSession]]:
    """Async context manager yielding an active AsyncSession or None if offline."""
    factory = get_session_factory()
    if factory is None:
        yield None
        return

    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def check_db_health() -> Dict[str, Any]:
    """Execute non-blocking database health check.
    
    Returns structured status without raising exceptions.
    """
    if not is_database_configured():
        return {
            "status": "unconfigured",
            "connected": False,
            "mode": "offline_in_memory",
            "dialect": "none",
            "pgvector_available": False,
            "detail": "DATABASE_URL is not set. Operating in in-memory fallback mode.",
        }

    engine = get_engine()
    if engine is None:
        return {
            "status": "failed_initialization",
            "connected": False,
            "mode": "offline_in_memory",
            "dialect": "none",
            "pgvector_available": False,
            "detail": "Failed to create database engine.",
        }

    try:
        async with engine.connect() as conn:
            # Check basic connection
            res = await conn.execute(text("SELECT 1"))
            res.scalar()

            # Check pgvector extension if PostgreSQL
            pgvector_supported = False
            if conn.dialect.name == "postgresql":
                try:
                    ext_check = await conn.execute(
                        text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                    )
                    pgvector_supported = ext_check.scalar() is not None
                except Exception:
                    pgvector_supported = False

            return {
                "status": "healthy",
                "connected": True,
                "mode": "postgresql" if conn.dialect.name == "postgresql" else conn.dialect.name,
                "dialect": conn.dialect.name,
                "pgvector_available": pgvector_supported,
                "detail": f"Database connected successfully via {conn.dialect.name}.",
            }
    except Exception as exc:
        logger.warning("Database health check ping failed: %s", exc)
        return {
            "status": "unavailable",
            "connected": False,
            "mode": "offline_in_memory",
            "dialect": engine.dialect.name if engine else "unknown",
            "pgvector_available": False,
            "detail": f"Connection failed: {exc}",
        }
