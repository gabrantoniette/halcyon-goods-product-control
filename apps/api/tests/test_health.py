"""The liveness endpoint a container healthcheck calls on a loop."""


def test_health_reports_a_reachable_database(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "up"


def test_health_reports_the_environment(client):
    assert client.get("/health").json()["environment"] == "test"


def test_health_reports_an_open_api_as_such(client):
    assert client.get("/health").json()["auth_required"] is False


def test_health_reports_a_closed_api_as_such(secured_client):
    assert secured_client.get("/health").json()["auth_required"] is True


def test_health_never_leaks_the_database_url_or_the_key(secured_client):
    """It is unauthenticated, so it must not describe how to reach anything."""
    body = secured_client.get("/health").text

    assert "sqlite" not in body.lower()
    assert "test-key" not in body
