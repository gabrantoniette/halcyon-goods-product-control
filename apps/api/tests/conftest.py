"""Shared fixtures for the API test suite.

Every test runs against a SQLite database held in memory, so the suite never
touches a real database and each test starts from an empty register.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from halcyon_api.config import Settings, get_settings
from halcyon_api.db import get_session
from halcyon_api.main import app

API_KEY = "test-key"


@pytest.fixture(name="session")
def session_fixture():
    """A session on a fresh in-memory database, thrown away after each test.

    StaticPool keeps every connection pointed at the same in-memory database:
    without it SQLite would hand out a new, empty one per connection and the
    tables created here would be invisible to the request under test.

    The tables are built from the metadata rather than by running Alembic,
    which keeps the suite fast; `test_migrations.py` is what proves the
    migrations and the models still agree.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(name="settings")
def settings_fixture():
    """Settings for a test run: in-memory database, authentication off."""
    return Settings(database_url="sqlite://", api_key=None, environment="test")


@pytest.fixture(name="client")
def client_fixture(session, settings):
    """A client for the API, wired to the in-memory session."""
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_settings] = lambda: settings

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture(name="api_key")
def api_key_fixture():
    """The key `secured_client` is configured with."""
    return API_KEY


@pytest.fixture(name="secured_client")
def secured_client_fixture(session):
    """A client for an API that has a key configured, so writes are closed.

    Mutually exclusive with `client`: both write to the same
    app.dependency_overrides, so a test that asks for both gets whichever was
    built last for both names. Use one or the other.
    """
    secured = Settings(database_url="sqlite://", api_key=API_KEY, environment="test")

    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_settings] = lambda: secured

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture(name="make_product")
def make_product_fixture():
    """Build a valid product body, overriding only the fields a test cares about."""

    def _make(**overrides):
        product = {
            "name": "Mechanical Keyboard 60%",
            "category": "Peripherals",
            "price": 89.90,
            "stock": 42,
            "in_stock": True,
            "rating": 4.7,
            "tags": ["gaming", "compact"],
        }
        product.update(overrides)
        return product

    return _make


@pytest.fixture(name="register")
def register_fixture(client, make_product):
    """Register a product through the API and return the stored record."""

    def _register(**overrides):
        product = make_product(**overrides)
        response = client.post(f"/products/{product['name']}", json=product)
        assert response.status_code == 201, response.text
        return response.json()

    return _register
