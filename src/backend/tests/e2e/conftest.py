import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="session")
def client():
    """
    Yield a TestClient instance for the API.
    """
    with TestClient(app) as c:
        yield c 