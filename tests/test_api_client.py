"""The HTTP access layer shared by the terminal menu and the web server.

The API answers one page at a time, but every caller works on the whole
register, so `list_products` resolves the paging here. What that walk does when
a page fails is the behaviour worth pinning down.
"""

import requests

from client.backend import api_client


def envelope(data=None, success=True, status_code=200):
    """The normalised result `try_response` would have produced."""
    return {
        "success": success,
        "status_code": status_code,
        "message": "",
        "detail": None,
        "data": data,
    }


class FakeResponse:
    """`list_products` only ever reads the paging headers off the response."""

    def __init__(self, total_pages):
        self.headers = {"X-Total-Pages": str(total_pages)}


def paged(monkeypatch, pages, total_pages=None, failing_page=None):
    """Make `_get_page` serve the given pages, optionally failing on one."""
    header_pages = len(pages) if total_pages is None else total_pages
    requested = []

    def fake_get_page(page):
        requested.append(page)
        if page == failing_page:
            return envelope(success=False, status_code=500), FakeResponse(header_pages)
        return envelope(data=pages[page - 1]), FakeResponse(header_pages)

    monkeypatch.setattr(api_client, "_get_page", fake_get_page)
    return requested


def test_a_single_page_is_returned_as_is(monkeypatch):
    paged(monkeypatch, [[{"name": "Keyboard"}, {"name": "Mouse"}]])

    result = api_client.list_products()

    assert result["success"] is True
    assert [product["name"] for product in result["data"]] == ["Keyboard", "Mouse"]


def test_every_page_is_walked_and_concatenated_in_order(monkeypatch):
    requested = paged(monkeypatch, [[{"name": "A"}], [{"name": "B"}], [{"name": "C"}]])

    result = api_client.list_products()

    assert requested == [1, 2, 3]
    assert [product["name"] for product in result["data"]] == ["A", "B", "C"]


def test_a_failed_page_aborts_the_walk_instead_of_returning_a_partial_set(monkeypatch):
    """Half the register reported as all of it would make every total wrong."""
    paged(monkeypatch, [[{"name": "A"}], [], [{"name": "C"}]], failing_page=2)

    result = api_client.list_products()

    assert result["success"] is False
    assert result["status_code"] == 500
    assert result["data"] is None


def test_a_failed_first_page_is_returned_untouched(monkeypatch):
    paged(monkeypatch, [[]], failing_page=1)

    result = api_client.list_products()

    assert result["success"] is False
    assert result["data"] is None


def test_an_empty_register_is_not_an_error(monkeypatch):
    paged(monkeypatch, [[]], total_pages=0)

    result = api_client.list_products()

    assert result["success"] is True
    assert result["data"] == []


def test_a_missing_paging_header_is_treated_as_a_single_page(monkeypatch):
    """An API that stopped sending the counter must not silently truncate."""

    def fake_get_page(page):
        response = FakeResponse(1)
        response.headers = {}
        return envelope(data=[{"name": "Keyboard"}]), response

    monkeypatch.setattr(api_client, "_get_page", fake_get_page)

    result = api_client.list_products()

    assert result["data"] == [{"name": "Keyboard"}]


def test_a_garbled_paging_header_is_treated_as_a_single_page(monkeypatch):
    def fake_get_page(page):
        response = FakeResponse(1)
        response.headers = {"X-Total-Pages": "not a number"}
        return envelope(data=[{"name": "Keyboard"}]), response

    monkeypatch.setattr(api_client, "_get_page", fake_get_page)

    assert api_client.list_products()["success"] is True


# ------------------------------------------------------------ health check


def test_is_api_up_is_false_when_the_api_refuses_the_connection(monkeypatch):
    def refuse(*args, **kwargs):
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr(api_client.r, "get", refuse)

    assert api_client.is_api_up() is False


def test_is_api_up_is_true_when_the_api_answers(monkeypatch):
    monkeypatch.setattr(api_client.r, "get", lambda *args, **kwargs: FakeResponse(1))

    assert api_client.is_api_up() is True


# ------------------------------------------------------------ url building


def test_urls_never_double_up_the_separator():
    assert api_client._url() == f"{api_client.API_BASE_URL}/products"
    assert api_client._url("Keyboard") == f"{api_client.API_BASE_URL}/products/Keyboard"
