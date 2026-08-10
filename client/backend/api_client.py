"""HTTP access layer to the internal product control API.

These functions know how to talk to the API and nothing else - they take plain
arguments and return the normalised dictionary produced by `try_response`.
Collecting user input is the caller's job, which is what lets both the terminal
menu and the web server share this module.
"""

import os
from pathlib import Path

import requests as r
from dotenv import load_dotenv

from .http_status import try_response

# The .env file lives at the project root (multibrand-store/), two levels up.
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH)

# rstrip so a trailing slash in .env does not produce '//products' below.
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

# Without a timeout a hung server would freeze the menu and the web request.
TIMEOUT = 5


def _url(*parts):
    return "/".join([API_BASE_URL, "products", *[str(part) for part in parts]])


def is_api_up():
    """Cheap health check used before opening the UI."""
    try:
        r.get(_url(), timeout=2)
    except r.RequestException:
        return False
    return True


def _get_page(page):
    """One page of products: the parsed envelope plus the raw response."""
    response = r.get(_url(), params={"page": page}, timeout=TIMEOUT)
    return try_response(response), response


def _total_pages(response):
    """Read the paging counter the API returns, defaulting to a single page."""
    try:
        return int(response.headers.get("X-Total-Pages", 1))
    except (TypeError, ValueError):
        return 1


def list_products():
    """Every product, walked page by page and returned as one envelope.

    The API answers in pages, but the callers all work on the full set - the
    dashboard's totals, chart and filters are computed over it - so the paging
    is resolved here instead of leaking into every caller.
    """
    result, response = _get_page(1)
    if not result["success"]:
        return result

    products = list(result["data"] or [])

    for page in range(2, _total_pages(response) + 1):
        page_result, _ = _get_page(page)
        # A failed page aborts the walk: half the records reported as all of
        # them would make every total on the dashboard wrong.
        if not page_result["success"]:
            return page_result
        products.extend(page_result["data"] or [])

    result["data"] = products
    return result


def get_products_by_name(name):
    return try_response(r.get(_url(name), timeout=TIMEOUT))


def create_product(name, product_data):
    return try_response(r.post(_url(name), json=product_data, timeout=TIMEOUT))


def replace_product(name, product_data):
    """Full update (PUT): every field must be present in the body."""
    return try_response(r.put(_url(name), json=product_data, timeout=TIMEOUT))


def update_product_fields(name, product_data):
    """Partial update (PATCH): only the changed fields are sent."""
    return try_response(r.patch(_url(name), json=product_data, timeout=TIMEOUT))


def delete_product(name):
    return try_response(r.delete(_url(name), timeout=TIMEOUT))
