from pathlib import Path
import time

import pytest
import pytest_asyncio
import shutil
from app.core.model.properties import CodePosition
# from app.core.model.nodes import ProjectNode
# from app.core.repository import Repositories
# from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
# from app.core.services.call_service import CallService
# from app.core.services.class_service import ClassService
from app.core.services.file_service import FileService
from app.core.services.folder_service import FolderService
# from app.core.services.function_service import FunctionService
from app.core.services.project_service import ProjectService


PROJECT_PATH = Path(__file__).resolve().parent / "sample_project"
DEFAULT_POSITION = CodePosition(
    line_no=1,
    col_offset=0,
    end_line_no=1,
    end_col_offset=0,
)


# @pytest_asyncio.fixture(autouse=True)
# async def _isolate_test_db(arangodb_client):
#     """
#     Ensure unit tests are isolated from each other.

#     The ArangoDB database is session-scoped (see tests/conftest.py), so documents
#     would otherwise leak between tests. Also, some repository methods run AQL
#     directly against edge collections without ensuring they exist first.
#     """
#     repos = Repositories(arangodb_client)

#     # Ensure required collections exist (correct types) before any AQL uses them.
#     await repos.nodes.get_collection()
#     await repos.contains_edges.get_collection()
#     await repos.targets_edges.get_collection()
#     await repos.log_to_function_edges.get_collection()
#     await repos.log_to_log_edges.get_collection()

#     # Truncate in edge->vertex order for cleanliness.
#     for name in [
#         "contains_edges",
#         "targets_edges",
#         "log_to_function_edges",
#         "log_to_log_edges",
#         "nodes",
#     ]:
#         col = arangodb_client.collection(name)
#         await col.truncate()

#     yield


# async def _create_function(function_service: FunctionService, name: str, qname: str):
#     return await function_service.create(
#         name,
#         qname,
#         f"This is {name.lower()}",
#         DEFAULT_POSITION,
#     )


# async def _create_class(class_service: ClassService, name: str, qname: str):
#     return await class_service.create(
#         name,
#         qname,
#         f"This is {name.lower()}",
#         DEFAULT_POSITION,
#     )


# async def _create_call(call_service: CallService, name: str, qname: str, target_id: str):
#     return await call_service.create(
#         name,
#         qname,
#         f"This is {name.lower()}",
#         DEFAULT_POSITION,
#         target_id,
#     )


# @pytest_asyncio.fixture()
# async def create_sample_project(arangodb_client, create_repos, tmp_path):
#     project_path = tmp_path / "project"
#     shutil.copytree(PROJECT_PATH, project_path)
#     project_node = ProjectNode(
#         name="Protector",
#         description="Protector is a tool for protecting your code.",
#         qname="protector",
#         current_version=int(time.time_ns()),
#         path=project_path.as_posix(),
#     )

#     db_path = tmp_path / "db" / project_node.name
#     db_path.parent.mkdir(parents=True, exist_ok=True)

#     project_service = ProjectService(create_repos)
#     project_node = await project_service.create_node(
#         project_node
#     )

#     orchestrator = GraphBuilderOrchestrator(
#         project_node=project_node,
#         db=arangodb_client,
#         ignore_file_name=None,
#     )
#     await orchestrator.resync()


@pytest_asyncio.fixture
async def create_project(create_repos):
    project_service = ProjectService(create_repos)
    project = await project_service.create(
        "Test Project",
        "This is a test project",
        "test_project"
    )
    yield project
    await project_service.delete(project.id)


@pytest_asyncio.fixture
async def create_folder(create_repos, create_project):
    folder_service = FolderService(create_repos, create_project)
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
async def create_file(create_repos, create_project):
    file_service = FileService(create_repos, create_project)
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

# @pytest.fixture
# def function_service(create_repos):
#     return FunctionService(create_repos)


# @pytest.fixture
# def class_service(create_repos):
#     return ClassService(create_repos)


# @pytest.fixture
# def call_service(create_repos):
#     return CallService(create_repos)


# @pytest_asyncio.fixture
# async def create_function(function_service):
#     return await _create_function(
#         function_service,
#         "Test Function",
#         "test_project.test_function",
#     )


# @pytest_asyncio.fixture
# async def create_function2(function_service):
#     return await _create_function(
#         function_service,
#         "Test Function 2",
#         "test_project.test_function2",
#     )


# @pytest_asyncio.fixture
# async def create_function3(function_service):
#     return await _create_function(
#         function_service,
#         "Test Function 3",
#         "test_project.test_function3",
#     )


# @pytest_asyncio.fixture
# async def create_class(class_service):
#     return await _create_class(
#         class_service,
#         "Test Class",
#         "test_project.test_class",
#     )


# @pytest_asyncio.fixture
# async def create_class2(class_service):
#     return await _create_class(
#         class_service,
#         "Test Class 2",
#         "test_project.test_class2",
#     )


# @pytest_asyncio.fixture
# async def create_call(call_service, create_function):
#     return await _create_call(
#         call_service,
#         "Test Call",
#         "test_project.test_call",
#         create_function.id,
#     )


# @pytest_asyncio.fixture
# async def create_call2(call_service, create_function2):
#     return await _create_call(
#         call_service,
#         "Test Call 2",
#         "test_project.test_call2",
#         create_function2.id,
#     )
