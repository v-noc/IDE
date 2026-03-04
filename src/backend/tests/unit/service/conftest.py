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
from app.core.services.code_element_service import CodeElementService
from app.core.model.nodes import ClassNode, FunctionNode


PROJECT_PATH = Path(__file__).resolve().parent / "sample_project"
DEFAULT_POSITION = CodePosition(
    line_no=1,
    col_offset=0,
    end_line_no=1,
    end_col_offset=0,
)


async def _create_function(function_service: FunctionService, id: str, name: str, qname: str):
    function_node = FunctionNode(
        id=id,
        name=name,
        qname=qname,
        description=f"This is {name.lower()}",
        code_position=DEFAULT_POSITION,
    )
    return await function_service.create(function_node)


async def _create_class(code_element_service: CodeElementService, id: str, name: str, qname: str):
    class_node = ClassNode(
        id=id,
        name=name,
        qname=qname,
        description=f"This is {name.lower()}",
        code_position=DEFAULT_POSITION,
    )
    return await code_element_service.create(class_node)


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
def code_element_service(project_uow):
    return CodeElementService(project_uow)


@pytest.fixture
def call_service(project_uow):
    return CallService(project_uow)


@pytest_asyncio.fixture
async def create_function(code_element_service):
    function = await _create_function(
        code_element_service,
        "FunctionSchema/function",
        "Test Function",
        "test_project.test_function",

    )
    yield function
    await code_element_service.delete(function.id)


@pytest_asyncio.fixture
async def create_function2(code_element_service):
    function = await _create_function(
        code_element_service,
        "FunctionSchema/function2",
        "Test Function 2",
        "test_project.test_function2",
    )
    yield function
    await code_element_service.delete(function.id)


@pytest_asyncio.fixture
async def create_function3(code_element_service):
    function3 = await _create_function(
        code_element_service,
        "FunctionSchema/function3",
        "Test Function 3",
        "test_project.test_function3",
    )
    yield function3
    await code_element_service.delete(function3.id)


@pytest_asyncio.fixture
async def create_class(code_element_service):

    class1 = await _create_class(
        code_element_service,
        "ClassSchema/class",
        "Test Class",
        "test_project.test_class",
    )
    yield class1
    await code_element_service.delete(class1.id)


@pytest_asyncio.fixture
async def create_class2(code_element_service):
    class2 = await _create_class(
        code_element_service,
        "ClassSchema/class2",
        "Test Class 2",
        "test_project.test_class2",
    )
    yield class2
    await code_element_service.delete(class2.id)


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
