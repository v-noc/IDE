import pytest
from fastapi.testclient import TestClient
from src.backend.app.main import app
from src.backend.app.db.dependencies import get_db_service
from src.backend.app.db.service import DatabaseService
from src.backend.app.models.user import User
from src.backend.app.models.follows import Follows

# Mock Managers
class MockUserManager:
    def __init__(self):
        self.data = {}

    def create(self, data):
        key = str(len(self.data) + 1)
        new_doc = User(**{"_key": key, **data.model_dump()})
        self.data[key] = new_doc
        return new_doc

    def get(self, key):
        return self.data.get(key)

    def find_by_email(self, email: str):
        for user in self.data.values():
            if user.email == email:
                return user
        return None

class MockFollowsManager:
    def __init__(self):
        self.data = {}

    def create(self, from_doc_id, to_doc_id, data):
        key = str(len(self.data) + 1)
        new_doc = Follows(**{"_key": key, "_from": from_doc_id, "_to": to_doc_id, **data.model_dump()})
        self.data[key] = new_doc
        return new_doc

# Mock Database Service
class MockDatabaseService:
    def __init__(self):
        self.users = MockUserManager()
        self.follows = MockFollowsManager()

def get_mock_db_service():
    return MockDatabaseService()

app.dependency_overrides[get_db_service] = get_mock_db_service

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

def test_follow_user():
    user1_res = client.post("/users", json={"username": "user1", "email": "user1@example.com"})
    user2_res = client.post("/users", json={"username": "user2", "email": "user2@example.com"})
    user1_key = user1_res.json()["_key"]
    user2_key = user2_res.json()["_key"]

    response = client.post(f"/users/{user1_key}/follows/{user2_key}")
    assert response.status_code == 200
    data = response.json()
    assert data["_from"] == f"users/{user1_key}"
    assert data["_to"] == f"users/{user2_key}"
