"""KALI Sentinel Database Package.

Exposes models, session helpers, and repository interfaces for audit & persistence.
"""

from kali_sentinel.database.models import (
    AgentMemoryRecord,
    DecisionRecord,
    SecurityRequestRecord,
    ToolExecutionRecord,
)
from kali_sentinel.database.repository import (
    InMemorySentinelRepository,
    SQLAlchemySentinelRepository,
    SentinelRepositoryInterface,
    get_sentinel_repository,
    sanitize_audit_data,
    set_repository_override,
)
from kali_sentinel.database.session import (
    check_db_health,
    get_database_url,
    get_db_session,
    get_engine,
    is_database_configured,
    is_database_required,
    set_engine_for_testing,
)

__all__ = [
    "SecurityRequestRecord",
    "DecisionRecord",
    "ToolExecutionRecord",
    "AgentMemoryRecord",
    "SentinelRepositoryInterface",
    "SQLAlchemySentinelRepository",
    "InMemorySentinelRepository",
    "get_sentinel_repository",
    "set_repository_override",
    "sanitize_audit_data",
    "get_database_url",
    "is_database_configured",
    "is_database_required",
    "get_engine",
    "get_db_session",
    "check_db_health",
    "set_engine_for_testing",
]
