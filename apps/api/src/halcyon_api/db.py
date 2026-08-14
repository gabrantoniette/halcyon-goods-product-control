"""Database engine and session.

The engine is built from `database_url`, so the same code runs on the SQLite
file used for local development and on the Postgres served by docker-compose.
Schema changes are Alembic's job - see apps/api/migrations.
"""

from collections.abc import Iterator

from sqlalchemy import Engine
from sqlmodel import Session, create_engine

from .config import Settings, get_settings


def build_engine(settings: Settings) -> Engine:
    """An engine tuned for whichever backend the URL points at."""
    if settings.is_sqlite:
        # SQLite refuses cross-thread use by default, and uvicorn serves
        # requests from a thread pool.
        return create_engine(settings.database_url, connect_args={"check_same_thread": False})

    # pool_pre_ping costs one round trip but avoids handing out a connection
    # the database closed while the app was idle - the usual cause of a
    # "server closed the connection unexpectedly" after a quiet night.
    return create_engine(settings.database_url, pool_pre_ping=True)


engine = build_engine(get_settings())


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
