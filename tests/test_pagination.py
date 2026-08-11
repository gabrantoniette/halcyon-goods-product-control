"""Paging on GET /products.

The clients rebuild the full register by walking pages, so the counters in the
headers and the stability of the ordering are load-bearing: a product that
appears on two pages, or on none, corrupts every total on the dashboard.
"""

import pytest

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 200


def register_many(client, make_product, count):
    """Register `count` products with predictable names."""
    for number in range(count):
        product = make_product(name=f"Item {number:03d}")
        response = client.post(f"/products/{product['name']}", json=product)
        assert response.status_code == 201, response.text


def counters(response):
    """The paging headers, as integers."""
    return {
        "page": int(response.headers["X-Page"]),
        "page_size": int(response.headers["X-Page-Size"]),
        "total_pages": int(response.headers["X-Total-Pages"]),
        "total_items": int(response.headers["X-Total-Items"]),
    }


def test_empty_register_reports_zero_pages(client):
    response = client.get("/products")

    assert response.status_code == 200
    assert response.json() == []
    assert counters(response)["total_items"] == 0
    assert counters(response)["total_pages"] == 0


def test_first_page_holds_the_default_page_size(client, make_product):
    register_many(client, make_product, 25)

    response = client.get("/products")

    assert len(response.json()) == DEFAULT_PAGE_SIZE
    assert counters(response) == {
        "page": 1,
        "page_size": DEFAULT_PAGE_SIZE,
        "total_pages": 3,
        "total_items": 25,
    }


def test_last_page_holds_the_remainder(client, make_product):
    register_many(client, make_product, 25)

    response = client.get("/products", params={"page": 3})

    assert len(response.json()) == 5
    assert counters(response)["page"] == 3


def test_page_size_is_honoured(client, make_product):
    register_many(client, make_product, 25)

    response = client.get("/products", params={"page_size": 25})

    assert len(response.json()) == 25
    assert counters(response)["total_pages"] == 1


def test_an_over_large_page_is_clamped_to_the_last_one(client, make_product):
    register_many(client, make_product, 25)

    response = client.get("/products", params={"page": 999})

    # The header must report the page actually served, not the one asked for,
    # or a client walking pages would never know where it landed.
    assert counters(response)["page"] == 3
    assert len(response.json()) == 5


def test_walking_every_page_yields_each_product_exactly_once(client, make_product):
    register_many(client, make_product, 25)

    seen = []
    first = client.get("/products")
    seen.extend(first.json())

    for page in range(2, counters(first)["total_pages"] + 1):
        seen.extend(client.get("/products", params={"page": page}).json())

    names = [product["name"] for product in seen]
    assert len(names) == 25
    assert len(set(names)) == 25
    assert names == sorted(names)


def test_paging_is_stable_across_repeated_requests(client, make_product):
    register_many(client, make_product, 25)

    first = client.get("/products", params={"page": 2}).json()
    again = client.get("/products", params={"page": 2}).json()

    assert first == again


@pytest.mark.parametrize(
    "params",
    [
        {"page": 0},
        {"page": -1},
        {"page_size": 0},
        {"page_size": MAX_PAGE_SIZE + 1},
    ],
)
def test_out_of_range_paging_arguments_are_rejected(client, params):
    assert client.get("/products", params=params).status_code == 422
