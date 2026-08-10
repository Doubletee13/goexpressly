from __future__ import annotations
"""
migrations/env.py — Alembic environment configuration.

Loads DATABASE_URL from app.config.settings (which reads .env),
and wires up the GoExpressly SQLAlchemy Base metadata so Alembic
can autogenerate accurate migrations from the ORM models.
"""
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Make sure `app` package is importable ────────────────────────────────
# Alembic runs from the `backend/` directory, but we add it explicitly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── App imports ───────────────────────────────────────────────────────────
from app.config import settings
from app.database import Base

# Import all models so their tables are registered on Base.metadata
import app.models  # noqa: F401

# ── Alembic Config object ────────────────────────────────────────────────
config = context.config

# Inject DATABASE_URL from settings (overrides blank value in alembic.ini)
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate support
target_metadata = Base.metadata


# ── Offline mode (generates SQL without DB connection) ───────────────────
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (connects to DB and applies migrations) ──────────────────
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
