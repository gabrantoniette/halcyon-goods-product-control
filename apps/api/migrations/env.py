"""Alembic environment.

The URL comes from the application settings rather than from alembic.ini, so
`alembic upgrade head` and the running API can never disagree about which
database they are pointed at.
"""

from logging.config import fileConfig

from alembic import context
from sqlmodel import SQLModel

from halcyon_api.config import get_settings
from halcyon_api.db import build_engine

# Importing the models is what puts the tables on SQLModel.metadata; without
# this line autogenerate would decide every table should be dropped.
from halcyon_api import models  # noqa: F401  isort:skip

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

settings = get_settings()


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running it, for review or a manual apply."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = build_engine(settings)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Without this a widened column or a changed type is silently
            # missed by autogenerate.
            compare_type=True,
            # SQLite cannot ALTER most things in place; batch mode rebuilds the
            # table instead, so the same revision runs on SQLite and Postgres.
            render_as_batch=settings.is_sqlite,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
