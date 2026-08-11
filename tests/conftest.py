"""Shared fixtures for the test suite.

Every test runs against a SQLite database held in memory, so the suite never
touches `database.db` and each test starts from an empty register.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from api.data import get_session
from api.main import app as api_app


@pytest.fixture(name="session")
def session_fixture():
    """A session on a fresh in-memory database, thrown away after each test.

    StaticPool keeps every connection pointed at the same in-memory database:
    without it SQLite would hand out a new, empty one per connection and the
    tables created here would be invisible to the request under test.
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


@pytest.fixture(name="client")
def client_fixture(session):
    """A client for the records API, wired to the in-memory session.

    TestClient is deliberately not used as a context manager: entering it would
    run the app's lifespan, and that calls `create_db_and_tables()` against the
    real file engine, creating `database.db` as a side effect of the tests.
    """
    api_app.dependency_overrides[get_session] = lambda: session

    yield TestClient(api_app)

    api_app.dependency_overrides.clear()


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
