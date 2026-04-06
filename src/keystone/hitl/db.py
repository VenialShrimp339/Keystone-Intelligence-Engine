"""Database engine and session factory for HITL infrastructure.

Provides async SQLAlchemy session management. The session factory is
configured once at startup and injected into FastAPI via dependency.

Phase 2 note: when migrating to Temporal, the DB layer stays the same.
Only the wait mechanism in gate.py changes (polling -> Temporal Signal).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from keystone.hitl.models import Base

# Module-level engine and session factory, initialized by init_db().
_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db(database_url: str) -> None:
    """Initialize the database engine and create tables if needed.

    Args:
        database_url: Async-compatible connection string.
            PostgreSQL: "postgresql+asyncpg://user:pass@host/db"
            SQLite (testing): "sqlite+aiosqlite:///path/to/db"
    """
    global _engine, _session_factory

    _engine = create_async_engine(database_url, echo=False)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def shutdown_db() -> None:
    """Dispose of the database engine. Call on application shutdown."""
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session. Used as a FastAPI dependency.

    Usage in FastAPI:
        @router.get("/gates")
        async def list_gates(session: AsyncSession = Depends(get_session)):
            ...
    """
    if _session_factory is None:
        msg = "Database not initialized. Call init_db() first."
        raise RuntimeError(msg)

    async with _session_factory() as session:
        yield session
