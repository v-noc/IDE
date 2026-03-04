from pathlib import Path
import time

import pytest
import pytest_asyncio
import shutil
from app.core.model.properties import CodePosition

from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator

from app.core.services.class_service import ClassService
from app.core.services.file_service import FileService
from app.core.services.folder_service import FolderService
from app.core.services.function_service import FunctionService
from app.core.services.project_service import ProjectService
from app.core.services.call_service import CallService
from app.core.model.nodes import ProjectNode


PROJECT_PATH = Path(__file__).resolve().parent / "sample_project"
DEFAULT_POSITION = CodePosition(
    line_no=1,
    col_offset=0,
    end_line_no=1,
    end_col_offset=0,
)


async def _create_function(function_service: FunctionService, id: str, name: str, qname: str):
    return await function_service.create(
        id,
        name,
        qname,
        f"This is {name.lower()}",
        DEFAULT_POSITION,
    )


async def _create_class(class_service: ClassService, id: str, name: str, qname: str):
    return await class_service.create(
        id,
        name,
        qname,
        f"This is {name.lower()}",
        DEFAULT_POSITION,
    )


async def _create_call(call_service: CallService, name: str, qname: str, target_id: str):
    return await call_service.create(
        name,
        qname,
        f"This is {name.lower()}",
        target_id,
    )


@pytest_asyncio.fixture()
async def create_sample_project(terminusdb_client, create_repos, tmp_path):
    project_path = tmp_path / "project"
    shutil.copytree(PROJECT_PATH, project_path)
    project_service = ProjectService(create_repos)
    project_node = await project_service.create(
        "Protector",
        "Protector is a tool for protecting your code.",
        project_path.as_posix(),
    )

    orchestrator = GraphBuilderOrchestrator(
        project_node=project_node,
        db=terminusdb_client,
        ignore_file_name=None,
    )
    await orchestrator.resync()

    yield project_node
    await project_service.delete(project_node.id)


@pytest_asyncio.fixture
async def project_uow_for_sample(terminusdb_client, create_sample_project):
    """ProjectUoW for tests that use create_sample_project (with orchestrator)."""
    from app.db.context import ProjectUoW, RequestDbContext

    ctx = RequestDbContext()
    return ProjectUoW(terminusdb_client, create_sample_project, ctx)


@pytest_asyncio.fixture
async def folder_service(project_uow):
    return FolderService(project_uow)


@pytest_asyncio.fixture
async def create_folder(folder_service):
    folder = await folder_service.create(
        "folder",
        "Test Folder",
        "test_project.test_folder",
        "This is a test folder",
        "test_folder"
    )
    yield folder
    await folder_service.delete(folder.id)


@pytest_asyncio.fixture
async def create_file2(project_uow):
    file_service = FileService(project_uow)
    file = await file_service.create(
        id="file2",
        name="Test File",
        qname="test_project.test_file",
        description="This is a test file",
        path="test_file",
        hash="hash"
    )
    yield file
    await file_service.delete(file.id)


@pytest_asyncio.fixture
async def create_file(project_uow):
    file_service = FileService(project_uow)
    file = await file_service.create(
        id="file",
        name="Test File",
        qname="test_project.test_file",
        description="This is a test file",
        path="test_file",
        hash="hash"
    )
    yield file
    await file_service.delete(file.id)


@pytest.fixture
def function_service(project_uow):
    return FunctionService(project_uow)


@pytest.fixture
def class_service(project_uow):
    return ClassService(project_uow)


@pytest.fixture
def call_service(project_uow):
    return CallService(project_uow)


@pytest_asyncio.fixture
async def create_function(function_service):
    function = await _create_function(
        function_service,
        "function",
        "Test Function",
        "test_project.test_function",
    )
    yield function
    await function_service.delete(function.id)


@pytest_asyncio.fixture
async def create_function2(function_service):
    function = await _create_function(
        function_service,
        "function2",
        "Test Function 2",
        "test_project.test_function2",
    )
    yield function
    await function_service.delete(function.id)


@pytest_asyncio.fixture
async def create_function3(function_service):
    function3 = await _create_function(
        function_service,
        "function3",
        "Test Function 3",
        "test_project.test_function3",
    )
    yield function3
    await function_service.delete(function3.id)


@pytest_asyncio.fixture
async def create_class(class_service):

    class1 = await _create_class(
        class_service,
        "class",
        "Test Class",
        "test_project.test_class",
    )
    yield class1
    await class_service.delete(class1.id)


@pytest_asyncio.fixture
async def create_class2(class_service):
    class2 = await _create_class(
        class_service,
        "class2",
        "Test Class 2",
        "test_project.test_class2",
    )
    yield class2
    await class_service.delete(class2.id)


@pytest_asyncio.fixture
async def create_call(call_service, create_function):
    call = await _create_call(
        call_service,
        "Test Call",
        "test_project.test_call",
        create_function.id,
    )
    yield call
    await call_service.delete(call.id)


@pytest_asyncio.fixture
async def create_call2(call_service, create_function2):
    call2 = await _create_call(
        call_service,
        "Test Call 2",
        "test_project.test_call2",
        create_function2.id,
    )
    yield call2
    await call_service.delete(call2.id)
