import pytest
from fastapi.testclient import TestClient
from src.backend.app.main import app
from src.backend.app.db.dependencies import get_user_collection
from src.backend.app.db.orm import CollectionManager
from src.backend.app.models.user import User

# Mock database
class MockCollectionManager(CollectionManager):
    def __init__(self, collection_name: str, model: type[User]):
        self.collection_name = collection_name
        self.model = model
        self.data = {}

    def create(self, data):
        key = str(len(self.data) + 1)
        new_doc = self.model(**{"_key": key, **data.model_dump()})
        self.data[key] = new_doc
        return new_doc

    def get(self, key):
        return self.data.get(key)

def get_mock_user_collection():
    return MockCollectionManager("users", User)

app.dependency_overrides[get_user_collection] = get_mock_user_collection

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

def test_create_user():
    response = client.post("/users", json={"username": "testuser", "email": "test@example.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "_key" in data
