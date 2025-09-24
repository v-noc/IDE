import pytest
from app.core.services.project_service import ProjectService
from app.core.repository import Repositories


@pytest.fixture
def create_repos(arangodb_client):
    return Repositories(arangodb_client)


@pytest.fixture
def create_project(create_repos):
    project_service = ProjectService(create_repos)
    return project_service.create(
        "Test Project",
        "This is a test project",
        "test_project"
    )
