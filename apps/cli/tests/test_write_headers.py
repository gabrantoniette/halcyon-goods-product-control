"""The API key the CLI attaches to the calls that change data.

Reads must go without it, so a client configured with no key can still browse
the register; writes must carry it whenever one is configured.
"""

import pytest

from halcyon_cli import api_client

HEADER = "X-API-Key"


class Recorder:
    """Captures the keyword arguments the client passes to requests."""

    def __init__(self):
        self.calls = []

    def __call__(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return Answer()

    @property
    def last_headers(self):
        return self.calls[-1].get("headers") or {}


class Answer:
    """A response `try_response` will read as a success."""

    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {}


@pytest.fixture(name="recorder")
def recorder_fixture(monkeypatch):
    recorder = Recorder()
    for method in ("get", "post", "put", "patch", "delete"):
        monkeypatch.setattr(api_client.r, method, recorder)
    return recorder


@pytest.fixture(name="with_key")
def with_key_fixture(monkeypatch):
    monkeypatch.setattr(api_client, "API_KEY", "a-configured-key")


WRITES = [
    ("create_product", ("Keyboard", {})),
    ("replace_product", ("Keyboard", {})),
    ("update_product_fields", ("Keyboard", {})),
    ("delete_product", ("Keyboard",)),
]


@pytest.mark.parametrize("function, args", WRITES)
def test_a_write_carries_the_key(recorder, with_key, function, args):
    getattr(api_client, function)(*args)

    assert recorder.last_headers[HEADER] == "a-configured-key"


@pytest.mark.parametrize("function, args", WRITES)
def test_a_write_sends_no_key_header_when_none_is_configured(recorder, monkeypatch, function, args):
    monkeypatch.setattr(api_client, "API_KEY", None)

    getattr(api_client, function)(*args)

    assert HEADER not in recorder.last_headers


@pytest.mark.parametrize("function, args", [("get_products_by_name", ("Keyboard",))])
def test_a_read_never_carries_the_key(recorder, with_key, function, args):
    getattr(api_client, function)(*args)

    assert HEADER not in recorder.last_headers


def test_the_health_check_asks_the_health_endpoint(recorder):
    api_client.is_api_up()

    assert recorder.calls[-1]["url"].endswith("/health")
