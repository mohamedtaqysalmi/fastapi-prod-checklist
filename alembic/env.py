"""Alembic environment.

Uses a sync SQLAlchemy engine. Async APP_DATABASE_URL values (sqlite+aiosqlite,
postgresql+asyncpg) are rewritten to their sync drivers for migrations.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.db import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _sync_url(url: str) -> str:
    replacements = (
        ("sqlite+aiosqlite://", "sqlite://"),
        ("postgresql+asyncpg://", "postgresql://"),
        ("postgres+asyncpg://", "postgresql://"),
    )
    for old, new in replacements:
        if url.startswith(old):
            return new + url[len(old) :]
    return url


def get_url() -> str:
    env_url = os.environ.get("APP_DATABASE_URL", "").strip()
    if env_url:
        return _sync_url(env_url)
    return config.get_main_option("sqlalchemy.url") or "sqlite:///./app.db"


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
