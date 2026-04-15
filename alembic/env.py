"""
Alembic async migration environment.
Supports Supabase, local PostgreSQL, and AWS RDS — just change DATABASE_URL in .env.
"""

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.models.models import Base  # noqa: F401
from app.core.config import settings

config = context.config

# ── Guard against placeholder DATABASE_URL ────────────────────────────────────
_url = settings.DATABASE_URL
_BAD = ["user:pass@localhost", "[YOUR-PASSWORD]", "xxxxxxxxxxxx", "your-rds-endpoint", "<<<"]
for _b in _BAD:
    if _b in _url:
        raise RuntimeError(
            "\n\n❌  DATABASE_URL in .env is still a placeholder!\n\n"
            "   Fix it first:\n"
            "   Local  : DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@localhost:5432/traveldb\n"
            "   Supabase: see .env.example Option B\n"
            "   Docker : run  docker-compose up --build  instead\n\n"
            "   Then run:  python check_setup.py\n"
        )

config.set_main_option("sqlalchemy.url", _url.replace("%", "%%"))
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
