"""The envelope every client call is normalised into.

`try_response` is the only place that decides whether a call succeeded, so the
web UI's toasts and the terminal menu's messages both inherit these rules.
"""

import json

import pytest
import requests

from halcyon_cli.http_status import describe_status, detail_of, read_body, try_response

ENVELOPE_KEYS = {"success", "status_code", "message", "detail", "data"}


def response_with(status_code, body=None, raw=None):
    """A real requests.Response carrying the given status and body."""
    response = requests.Response()
    response.status_code = status_code
    response.reason = "Test"
    response.url = "http://127.0.0.1:8000/products"
    if raw is not None:
        response._content = raw
    else:
        response._content = json.dumps(body).encode()
    return response


class UnreachableResponse:
    """Stands in for a request that never got an answer at all."""

    status_code = None

    def raise_for_status(self):
        raise requests.ConnectionError("connection refused")


# ---------------------------------------------------------------- successes


@pytest.mark.parametrize("status_code", [200, 201])
def test_a_successful_response_carries_the_body(status_code):
    result = try_response(response_with(status_code, {"name": "Keyboard"}))

    assert result["success"] is True
    assert result["status_code"] == status_code
    assert result["detail"] is None
    assert result["data"] == {"name": "Keyboard"}


def test_every_result_has_the_same_shape():
    ok = try_response(response_with(200, {}))
    failed = try_response(response_with(404, {"detail": "Product not found."}))
    unreachable = try_response(UnreachableResponse())

    assert set(ok) == set(failed) == set(unreachable) == ENVELOPE_KEYS


# ----------------------------------------------------------------- failures


def test_an_error_response_surfaces_the_api_detail():
    body = {"detail": "A product with this name already exists."}

    result = try_response(response_with(409, body))

    assert result["success"] is False
    assert result["status_code"] == 409
    assert result["detail"] == body["detail"]
    assert "Conflict" in result["message"]


def test_an_unreachable_api_reports_no_status_code():
    result = try_response(UnreachableResponse())

    assert result["success"] is False
    assert result["status_code"] is None
    assert result["data"] is None
    assert "Could not reach the API" in result["message"]


def test_a_body_that_is_not_json_becomes_no_data():
    result = try_response(response_with(500, raw=b"<html>Gateway</html>"))

    assert result["success"] is False
    assert result["data"] is None
    assert result["detail"] is None


def test_an_error_without_a_detail_field_still_reports_the_status():
    result = try_response(response_with(400, {"error": "something else"}))

    assert result["success"] is False
    assert result["detail"] is None
    assert "Bad Request" in result["message"]


# ------------------------------------------------------------------ helpers


def test_a_mapped_status_is_explained_in_words():
    assert "Conflict" in describe_status(409)


def test_an_unmapped_status_says_so_instead_of_raising():
    assert "not mapped" in describe_status(418)


def test_detail_of_ignores_bodies_that_are_not_objects():
    assert detail_of(["a", "list"]) is None
    assert detail_of(None) is None


def test_read_body_returns_none_for_a_non_json_body():
    assert read_body(response_with(200, raw=b"not json")) is None
