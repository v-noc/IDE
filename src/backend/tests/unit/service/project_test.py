from datetime import datetime, timezone
from app.core.services.project_service import ProjectService
# from app.core.services.folder_service import FolderService
# from app.core.services.file_service import FileService
# from app.core.services.function_service import FunctionService
# from app.core.services.document_service import DocumentService
# from app.core.services.log_service import LogService
# from app.core.model.properties import CodePosition
# from app.api.json_rpc.schemas import RegisterLogsParams, LogEventType
import pytest


@pytest.mark.asyncio
async def test_create_project(create_repos):
    print("creating project test")

    project_service = ProjectService(
        create_repos
    )

    created_project = await project_service.create(
        "Test Project",
        "This is a test project",
        "test_project"
    )

    assert created_project is not None
    assert created_project.name == "Test Project"
    assert "test-project" in created_project.db_name
    assert created_project.description == "This is a test project"

    await project_service.delete(created_project.id)


@pytest.mark.asyncio
async def test_get_project(create_repos, create_project):
    print("getting project test")

    project_service = ProjectService(
        create_repos
    )

    projects = await project_service.get_all()

    assert len(projects) == 1


@pytest.mark.asyncio
async def test_update_project(create_project, create_repos):

    project_service = ProjectService(
        create_repos
    )

    create_project.name = "Updated Project"
    create_project.description = "This is an updated project"
    create_project.local_path = "updated_project"

    await project_service.update(
        create_project
    )
    updated_project = await project_service.get(create_project.id)
    assert updated_project is not None
    assert updated_project["name"] == "Updated Project"
    assert updated_project["description"] == "This is an updated project"
    assert updated_project["local_path"] == "updated_project"


@pytest.mark.asyncio
async def test_delete_project(create_project, create_repos):
    project_service = ProjectService(
        create_repos
    )

    projects = await project_service.get_all()

    await project_service.delete(
        create_project.id
    )

    projects = await project_service.get_all()

    assert len(projects) == 0
