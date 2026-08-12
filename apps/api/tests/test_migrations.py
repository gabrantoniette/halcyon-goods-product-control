"""The migrations must describe the same schema the models do.

The rest of the suite builds its tables straight from the metadata, which is
fast but would happily pass while the migrations rotted. This is the test that
would catch a model field added without a revision to go with it.
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlmodel import SQLModel, create_engine

API_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(name="alembic_config")
def alembic_config_fixture(tmp_path, monkeypatch):
    """Alembic pointed at a throwaway SQLite file."""
    database_url = f"sqlite:///{tmp_path / 'migrated.db'}"

    # env.py reads the URL from the settings, so this is what redirects it.
    monkeypatch.setenv("HALCYON_DATABASE_URL", database_url)
    # The settings are cached, and the cache is shared across tests.
    from halcyon_api.config import get_settings

    get_settings.cache_clear()

    config = Config(str(API_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(API_DIR / "migrations"))

    yield config, database_url

    get_settings.cache_clear()


def test_upgrade_head_builds_the_schema_the_models_describe(alembic_config):
    """Run the migrations, then diff the result against the models."""
    config, database_url = alembic_config

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        difference = compare_metadata(context, SQLModel.metadata)
    engine.dispose()

    assert difference == [], f"models and migrations disagree: {difference}"


def test_downgrade_undoes_the_schema(alembic_config):
    """A revision that cannot be rolled back is a revision you cannot deploy."""
    config, database_url = alembic_config

    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = create_engine(database_url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        tables = context.connection.dialect.get_table_names(connection)
    engine.dispose()

    assert "product" not in tables
