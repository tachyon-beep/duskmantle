from __future__ import annotations

from fastapi.testclient import TestClient

from gateway.api.app import create_app


def test_health_endpoint_returns_ok() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint_returns_ready() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
