"""Endpoint behaviour for /products.

Products are addressed by name, so the rules that keep names unambiguous — the
409 on a duplicate and the 422 when the path and the body disagree — are what
most of these tests are about.
"""

from uuid import UUID

import pytest

# The stored row carries an `id` primary key, but ProductRead does not expose it.
PUBLIC_FIELDS = {"name", "category", "price", "stock", "in_stock", "rating", "tags", "uuid"}


# ------------------------------------------------------------------- create


def test_create_returns_201_and_the_stored_product(client, make_product):
    product = make_product()

    response = client.post(f"/products/{product['name']}", json=product)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == product["name"]
    assert body["price"] == product["price"]
    assert body["tags"] == product["tags"]


def test_create_assigns_a_uuid(client, make_product):
    product = make_product()

    body = client.post(f"/products/{product['name']}", json=product).json()

    # Parsing is the assertion: a malformed uuid raises.
    UUID(body["uuid"])


def test_create_never_exposes_the_primary_key(client, make_product):
    product = make_product()

    body = client.post(f"/products/{product['name']}", json=product).json()

    assert set(body) == PUBLIC_FIELDS
    assert "id" not in body


def test_create_rejects_a_body_name_that_disagrees_with_the_path(client, make_product):
    product = make_product(name="Body Name")

    response = client.post("/products/Path Name", json=product)

    assert response.status_code == 422
    assert "does not match" in response.json()["detail"]


def test_create_rejects_a_duplicate_name(client, register, make_product):
    register()
    duplicate = make_product(category="Something else")

    response = client.post(f"/products/{duplicate['name']}", json=duplicate)

    assert response.status_code == 409


def test_create_rejects_a_body_missing_a_required_field(client, make_product):
    product = make_product()
    del product["price"]

    response = client.post(f"/products/{product['name']}", json=product)

    assert response.status_code == 422


# ---------------------------------------------------------------------- read


def test_get_by_name_returns_the_product(client, register):
    stored = register()

    response = client.get(f"/products/{stored['name']}")

    assert response.status_code == 200
    assert response.json() == stored


def test_get_by_name_404s_when_nothing_matches(client):
    response = client.get("/products/Nothing Registered")

    assert response.status_code == 404


def test_get_by_name_is_exact_not_a_prefix_match(client, register):
    register(name="Keyboard")

    assert client.get("/products/Key").status_code == 404


# ----------------------------------------------------------------- replace


def test_put_replaces_every_field(client, register, make_product):
    stored = register()
    replacement = make_product(
        name=stored["name"],
        category="Audio",
        price=12.5,
        stock=3,
        in_stock=False,
        rating=2.0,
        tags=["clearance"],
    )

    response = client.put(f"/products/{stored['name']}", json=replacement)

    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "Audio"
    assert body["price"] == 12.5
    assert body["in_stock"] is False
    assert body["tags"] == ["clearance"]
    # Replacing the contents must not mint a new identity for the record.
    assert body["uuid"] == stored["uuid"]


def test_put_can_rename_a_product(client, register, make_product):
    register(name="Old Name")

    response = client.put("/products/Old Name", json=make_product(name="New Name"))

    assert response.status_code == 200
    assert response.json()["name"] == "New Name"
    assert client.get("/products/Old Name").status_code == 404
    assert client.get("/products/New Name").status_code == 200


def test_put_keeping_the_same_name_is_not_a_conflict(client, register, make_product):
    """Renaming a product to the name it already has must not clash with itself."""
    stored = register()

    response = client.put(f"/products/{stored['name']}", json=make_product(price=1.0))

    assert response.status_code == 200


def test_put_rejects_renaming_onto_another_product(client, register, make_product):
    register(name="Keyboard")
    register(name="Mouse")

    response = client.put("/products/Mouse", json=make_product(name="Keyboard"))

    assert response.status_code == 409


def test_put_404s_when_the_product_does_not_exist(client, make_product):
    response = client.put("/products/Ghost", json=make_product(name="Ghost"))

    assert response.status_code == 404


# ------------------------------------------------------------------- patch


def test_patch_changes_only_the_fields_that_were_sent(client, register):
    stored = register()

    response = client.patch(f"/products/{stored['name']}", json={"stock": 7})

    assert response.status_code == 200
    body = response.json()
    assert body["stock"] == 7
    assert body["category"] == stored["category"]
    assert body["price"] == stored["price"]
    assert body["tags"] == stored["tags"]


def test_patch_accepts_an_empty_body_as_a_no_op(client, register):
    stored = register()

    response = client.patch(f"/products/{stored['name']}", json={})

    assert response.status_code == 200
    assert response.json() == stored


@pytest.mark.parametrize(
    "field, value",
    [
        ("stock", 0),
        ("in_stock", False),
        ("price", 0.0),
        ("rating", 0.0),
        ("tags", []),
    ],
)
def test_patch_applies_falsy_values(client, register, field, value):
    """`exclude_none` must not swallow 0, False or an empty list."""
    stored = register()

    response = client.patch(f"/products/{stored['name']}", json={field: value})

    assert response.status_code == 200
    assert response.json()[field] == value


def test_patch_rejects_renaming_onto_another_product(client, register):
    register(name="Keyboard")
    register(name="Mouse")

    response = client.patch("/products/Mouse", json={"name": "Keyboard"})

    assert response.status_code == 409


def test_patch_404s_when_the_product_does_not_exist(client):
    assert client.patch("/products/Ghost", json={"stock": 1}).status_code == 404


# ------------------------------------------------------------------ delete


def test_delete_returns_a_receipt_carrying_the_uuid(client, register):
    stored = register()

    response = client.delete(f"/products/{stored['name']}")

    assert response.status_code == 200
    body = response.json()
    assert body["uuid"] == stored["uuid"]
    assert stored["name"] in body["message"]


def test_delete_removes_the_product(client, register):
    stored = register()

    client.delete(f"/products/{stored['name']}")

    assert client.get(f"/products/{stored['name']}").status_code == 404


def test_delete_404s_when_the_product_does_not_exist(client):
    assert client.delete("/products/Ghost").status_code == 404


def test_delete_frees_the_name_for_reuse(client, register, make_product):
    stored = register()
    client.delete(f"/products/{stored['name']}")

    response = client.post(f"/products/{stored['name']}", json=make_product())

    assert response.status_code == 201
