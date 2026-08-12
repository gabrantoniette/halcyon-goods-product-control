"""Settings read from the environment.

These exist because the container did what the suite could not: it set the
variables for real. `HALCYON_CORS_ORIGINS=http://localhost:3000` crashed the
API at import time, because pydantic-settings JSON-decodes a list-typed field
at the source, before any validator runs.
"""

import pytest

from halcyon_api.config import Settings


@pytest.fixture(name="env")
def env_fixture(monkeypatch):
    """Set HALCYON_* variables for one test."""

    def _set(**values):
        for name, value in values.items():
            monkeypatch.setenv(f"HALCYON_{name.upper()}", value)

    return _set


def test_a_comma_separated_list_is_accepted(env):
    """The form a .env file or a compose file would naturally use."""
    env(cors_origins="http://localhost:3000,https://halcyon.example")

    assert Settings().cors_origins == ["http://localhost:3000", "https://halcyon.example"]


def test_a_single_origin_is_accepted(env):
    env(cors_origins="http://localhost:3000")

    assert Settings().cors_origins == ["http://localhost:3000"]


def test_a_json_list_is_still_accepted(env):
    env(cors_origins='["http://a.test", "http://b.test"]')

    assert Settings().cors_origins == ["http://a.test", "http://b.test"]


def test_surrounding_whitespace_is_trimmed(env):
    env(cors_origins=" http://a.test , http://b.test ")

    assert Settings().cors_origins == ["http://a.test", "http://b.test"]


def test_an_empty_value_yields_no_origins(env):
    env(cors_origins="")

    assert Settings().cors_origins == []


def test_the_default_is_the_local_dashboard():
    assert Settings().cors_origins == ["http://localhost:3000"]


# --------------------------------------------------------------- other fields


def test_the_database_url_is_read_from_the_environment(env):
    env(database_url="postgresql+psycopg://user:pw@db:5432/halcyon")

    settings = Settings()
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.is_sqlite is False


def test_sqlite_is_detected(env):
    env(database_url="sqlite:///./database.db")

    assert Settings().is_sqlite is True


def test_auth_is_off_when_the_key_is_empty(env):
    env(api_key="")

    assert Settings().auth_enabled is False


def test_auth_is_on_when_a_key_is_set(env):
    env(api_key="a-key")

    assert Settings().auth_enabled is True
