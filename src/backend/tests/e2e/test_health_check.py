# tests/e2e/test_health_check.py

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """
    Tests that the health check endpoint returns a 200 OK response.
    """
    response = await client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
