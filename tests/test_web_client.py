"""The client's own backend, which the browser talks to.

Its whole job is to relay: the envelope from `api_client` must reach the browser
unchanged, and the API's status code must survive the hop, because that is what
the front-end switches its toasts on.
"""

import pytest
from fastapi.testclient import TestClient

from client.backend import api_client, server

SERVICE_UNAVAILABLE = 503


@pytest.fixture(name="web")
def web_fixture():
    return TestClient(server.app)


def envelope(success=True, status_code=200, data=None, detail=None):
    return {
        "success": success,
        "status_code": status_code,
        "message": "a message",
        "detail": detail,
        "data": data,
    }


def test_the_envelope_reaches_the_browser_unchanged(web, monkeypatch):
    result = envelope(data=[{"name": "Keyboard"}])
    monkeypatch.setattr(api_client, "list_products", lambda: result)

    response = web.get("/api/products")

    assert response.status_code == 200
    assert response.json() == result


@pytest.mark.parametrize("status_code", [404, 409, 422])
def test_an_api_error_keeps_its_status_code(web, monkeypatch, status_code):
    monkeypatch.setattr(
        api_client,
        "get_products_by_name",
        lambda name: envelope(success=False, status_code=status_code),
    )

    response = web.get("/api/products/Keyboard")

    assert response.status_code == status_code
    assert response.json()["success"] is False


def test_an_unreachable_api_becomes_a_503(web, monkeypatch):
    """There is no status code to forward, so the relay supplies its own."""
    monkeypatch.setattr(api_client, "list_products", lambda: envelope(success=False, status_code=None))

    response = web.get("/api/products")

    assert response.status_code == SERVICE_UNAVAILABLE


def test_create_forwards_the_name_and_the_body(web, monkeypatch):
    seen = {}

    def fake_create(name, product_data):
        seen["name"] = name
        seen["body"] = product_data
        return envelope(status_code=201, data=product_data)

    monkeypatch.setattr(api_client, "create_product", fake_create)
    body = {"name": "Keyboard", "price": 89.9}

    response = web.post("/api/products/Keyboard", json=body)

    assert response.status_code == 201
    assert seen == {"name": "Keyboard", "body": body}


@pytest.mark.parametrize(
    "method, function",
    [
        ("put", "replace_product"),
        ("patch", "update_product_fields"),
    ],
)
def test_updates_forward_the_body(web, monkeypatch, method, function):
    seen = {}
    monkeypatch.setattr(
        api_client,
        function,
        lambda name, product_data: seen.update(name=name, body=product_data) or envelope(),
    )

    response = getattr(web, method)("/api/products/Keyboard", json={"stock": 3})

    assert response.status_code == 200
    assert seen == {"name": "Keyboard", "body": {"stock": 3}}


def test_delete_forwards_the_name(web, monkeypatch):
    monkeypatch.setattr(api_client, "delete_product", lambda name: envelope(data={"uuid": name}))

    response = web.delete("/api/products/Keyboard")

    assert response.status_code == 200
    assert response.json()["data"] == {"uuid": "Keyboard"}


def test_a_name_with_a_slash_or_a_space_survives_the_hop(web, monkeypatch):
    seen = {}
    monkeypatch.setattr(
        api_client,
        "get_products_by_name",
        lambda name: seen.update(name=name) or envelope(),
    )

    web.get("/api/products/Mechanical%20Keyboard%2060%25")

    assert seen["name"] == "Mechanical Keyboard 60%"


# -------------------------------------------------------------------- health


def test_health_reports_the_api_state_and_address(web, monkeypatch):
    monkeypatch.setattr(api_client, "is_api_up", lambda: True)

    body = web.get("/api/health").json()

    assert body == {"api_up": True, "api_base_url": api_client.API_BASE_URL}


def test_health_is_still_answered_when_the_api_is_down(web, monkeypatch):
    monkeypatch.setattr(api_client, "is_api_up", lambda: False)

    response = web.get("/api/health")

    assert response.status_code == 200
    assert response.json()["api_up"] is False


# ------------------------------------------------------------------ frontend


def test_the_frontend_is_served_at_the_root(web):
    response = web.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_the_api_routes_win_over_the_static_mount(web, monkeypatch):
    """The mount at '/' is last, so it must not shadow /api/*."""
    monkeypatch.setattr(api_client, "is_api_up", lambda: True)

    assert web.get("/api/health").json()["api_up"] is True
