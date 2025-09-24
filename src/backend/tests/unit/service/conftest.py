import pytest
from app.core.services.project_service import ProjectService
from app.core.repository import Repositories
from app.core.services.folder_service import FolderService
from app.core.services.file_service import FileService
from app.core.services.function_service import FunctionService
from app.core.model.properties import CodePosition


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


@pytest.fixture
def create_folder(create_repos):
    folder_service = FolderService(create_repos)
    return folder_service.create(
        "Test Folder",
        "test_project.test_folder",
        "This is a test folder",
        "test_folder"
    )


@pytest.fixture
def create_file(create_repos):
    file_service = FileService(create_repos)
    return file_service.create(
        "Test File",
        "test_project.test_file",
        "This is a test file",
        "test_file"
    )


@pytest.fixture
def create_function(create_repos):
    function_service = FunctionService(create_repos)
    position = CodePosition(
        line_no=1,
        col_offset=0,
        end_line_no=1,
        end_col_offset=0
    )
    return function_service.create(
        "Test Function",
        "test_project.test_function",
        "This is a test function",
        "test_function",
        position
    )


@pytest.fixture
def create_function2(create_repos):
    function_service = FunctionService(create_repos)
    position = CodePosition(
        line_no=1,
        col_offset=0,
        end_line_no=1,
        end_col_offset=0
    )
    return function_service.create(
        "Test Function 2",
        "test_project.test_function2",
        "This is a test function",
        "test_function",
        position
    )
