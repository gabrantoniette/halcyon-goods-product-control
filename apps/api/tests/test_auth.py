"""The API key check on the endpoints that change data.

Reads stay open so a dashboard can be pointed at the API without a secret;
everything that writes needs the key.
"""

import pytest

HEADER = "X-API-Key"

WRITES = [
    ("post", "/products/New Item"),
    ("put", "/products/New Item"),
    ("patch", "/products/New Item"),
    ("delete", "/products/New Item"),
]


def call(client, method, path, key=None):
    headers = {HEADER: key} if key else {}
    if method == "delete":
        return client.delete(path, headers=headers)
    return getattr(client, method)(path, json={}, headers=headers)


@pytest.mark.parametrize("method, path", WRITES)
def test_a_write_without_the_key_is_rejected(secured_client, method, path):
    response = call(secured_client, method, path)

    assert response.status_code == 401
    assert HEADER in response.json()["detail"]


@pytest.mark.parametrize("method, path", WRITES)
def test_a_write_with_the_wrong_key_is_forbidden(secured_client, method, path):
    response = call(secured_client, method, path, key="not-the-key")

    assert response.status_code == 403


def test_the_right_key_gets_through(secured_client, make_product, api_key):
    product = make_product()

    response = secured_client.post(
        f"/products/{product['name']}",
        json=product,
        headers={HEADER: api_key},
    )

    assert response.status_code == 201


@pytest.mark.parametrize("path", ["/products", "/products/Anything", "/health"])
def test_reads_never_ask_for_a_key(secured_client, path):
    """A missing product is still a 404, not a 401 - reads are open."""
    assert secured_client.get(path).status_code in {200, 404}


def test_authentication_is_off_when_no_key_is_configured(client, make_product):
    """A bare `uvicorn` and the test suite stay frictionless."""
    product = make_product()

    response = client.post(f"/products/{product['name']}", json=product)

    assert response.status_code == 201


def test_the_key_is_never_echoed_back(secured_client, api_key):
    response = call(secured_client, "post", "/products/New Item", key="not-the-key")

    assert api_key not in response.text
    assert "not-the-key" not in response.text
