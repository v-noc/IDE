# tests/e2e/test_health_check.py

from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """
    Tests that the health check endpoint returns a 200 OK response.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
