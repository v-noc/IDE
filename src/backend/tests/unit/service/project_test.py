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

from app.core.model.schemas import FileSchema


@pytest.mark.asyncio
async def test_create_project(empty_project_uow):
    print("creating project test")

    project_service = ProjectService(
        empty_project_uow
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
async def test_get_project(project_uow):
    print("getting project test")

    project_service = ProjectService(
        project_uow
    )

    projects = await project_service.get_all()

    assert len(projects) == 1


@pytest.mark.asyncio
async def test_update_project(create_project, project_uow):

    project_service = ProjectService(
        project_uow
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
async def test_delete_project(project_uow):
    project_service = ProjectService(
        project_uow
    )

    projects = await project_service.get_all()

    await project_service.delete(
        project_uow.project.id
    )

    projects = await project_service.get_all()

    assert len(projects) == 0


@pytest.mark.asyncio
async def test_get_children(create_project, project_uow, create_file, create_folder, create_function, create_class, create_call):
    project_service = ProjectService(project_uow)

    children = await project_service.get_children([FileSchema.__name__])
    # print(children)

    assert len(children) == 4

    for child in children:
        assert type(child) != FileSchema
