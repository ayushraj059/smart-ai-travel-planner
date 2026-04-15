"""
Async SQLAlchemy engine + session factory.
DATABASE_URL from .env — works with local Postgres, Supabase, or AWS RDS.

FIXES:
  1. get_db_optional() correctly yields None when DB is unavailable,
     without breaking FastAPI's generator dependency contract.
  2. Supabase asyncpg ssl=require injected automatically.
  3. Lazy engine creation — startup never fails on bad credentials.
  4. Password special chars in .env: @ → %%40, # → %%23
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.models import Base  # noqa: F401 — needed by Alembic autogenerate

logger = logging.getLogger(__name__)

_engine = None
_AsyncSessionLocal = None
_db_available = None  # None=untested  True=ok  False=failed


def _get_session_factory():
    """Return session factory, or None if DB is not configured/reachable."""
    global _engine, _AsyncSessionLocal, _db_available

    if _db_available is False:
        return None
    if _AsyncSessionLocal is not None:
        return _AsyncSessionLocal
    if not settings.DATABASE_URL:
        logger.warning("DATABASE_URL not set — persistence disabled.")
        _db_available = False
        return None

    url = settings.DATABASE_URL
    connect_args = {}
    if "supabase.co" in url:
        connect_args["ssl"] = "require"
        logger.info("Supabase detected — SSL enabled.")

    try:
        _engine = create_async_engine(
            url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            connect_args=connect_args,
        )
        _AsyncSessionLocal = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        logger.info("DB engine initialised.")
        return _AsyncSessionLocal
    except Exception as e:
        logger.error(f"DB engine creation failed: {e}")
        _db_available = False
        return None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — required DB session. Raises if unavailable."""
    factory = _get_session_factory()
    if factory is None:
        raise RuntimeError("Database not configured. Check DATABASE_URL in .env.")
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_optional() -> AsyncGenerator[Optional[AsyncSession], None]:
    """
    FastAPI dependency — yields AsyncSession OR None.

    CRITICAL FastAPI generator rule:
      - Must always yield exactly once.
      - Must never raise inside the generator body (after yield).
      - Exceptions after yield are handled in the finally block only.

    Behaviour:
      DB available  → yields session, commits, returns normally.
      DB down       → yields None immediately (no session opened).
      DB save fails → session is rolled back, warning logged.
                      The route already sent its response, so no 500 is raised.
    """
    global _db_available
    factory = _get_session_factory()

    if factory is None:
        # No DB configured — yield None and exit cleanly
        yield None
        return

    session = factory()
    try:
        yield session           # <-- route handler runs here
        await session.commit()
        _db_available = True
    except Exception as e:
        _db_available = False
        try:
            await session.rollback()
        except Exception:
            pass
        logger.warning(
            f"DB save skipped (itinerary still returned to user). "
            f"{type(e).__name__}: {e}"
        )
        # Do NOT re-raise — FastAPI has already sent the response.
        # Re-raising here would cause "No response object" ASGI crash.
    finally:
        try:
            await session.close()
        except Exception:
            pass
