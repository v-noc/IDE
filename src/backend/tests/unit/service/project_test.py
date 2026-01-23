from datetime import datetime, timezone
from app.core.services.project_service import ProjectService
from app.core.services.folder_service import FolderService
from app.core.services.file_service import FileService
from app.core.services.function_service import FunctionService
from app.core.services.document_service import DocumentService
from app.core.services.log_service import LogService
from app.core.model.properties import CodePosition
from app.api.json_rpc.schemas import RegisterLogsParams, LogEventType
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
    assert created_project.qname == "test_project"
    assert created_project.description == "This is a test project"


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
    create_project.path = "updated_project"

    updated_project = await project_service.update(
        create_project
    )

    assert updated_project is not None
    assert updated_project.name == "Updated Project"
    assert updated_project.description == "This is an updated project"
    assert updated_project.path == "updated_project"


@pytest.mark.asyncio
async def test_delete_project(create_project, create_repos):
    project_service = ProjectService(
        create_repos
    )

    projects = await project_service.get_all()

    await project_service.delete(
        create_project
    )

    projects = await project_service.get_all()

    assert len(projects) == 0


@pytest.mark.asyncio
async def test_add_folder_to_project(
    create_project, create_folder, create_repos
):
    project_service = ProjectService(
        create_repos
    )

    await project_service.add_folder(
        create_project.id,
        create_folder.id
    )

    children = await project_service.get_children(
        create_project.id
    )

    assert len(children) == 1


@pytest.mark.asyncio
async def test_add_file_to_project(create_project, create_file, create_repos):
    project_service = ProjectService(
        create_repos
    )

    await project_service.add_file(
        create_project.id,
        create_file.id
    )

    children = await project_service.get_children(
        create_project.id
    )

    assert len(children) == 1


@pytest.mark.asyncio
async def test_cascade_delete_project(
    create_project, create_folder, create_file, create_repos
):
    """Test that deleting a project also deletes all its children."""
    project_service = ProjectService(create_repos)

    # Add folder and file to the project
    await project_service.add_folder(
        create_project.id,
        create_folder.id
    )
    await project_service.add_file(
        create_project.id,
        create_file.id
    )

    # Verify project has children
    children = await project_service.get_children(create_project.id)
    assert len(children) == 2

    # Store IDs for verification after deletion
    project_key = create_project.key
    folder_key = create_folder.key
    file_key = create_file.key

    # Delete the project (should cascade delete children)
    deleted = await project_service.delete(create_project)
    assert deleted is True

    # Verify project is deleted
    project_node = await create_repos.project_repo.get_by_key(project_key)
    assert project_node is None

    # Verify folder is deleted (cascade)
    folder_node = await create_repos.folder_repo.get_by_key(folder_key)
    assert folder_node is None

    # Verify file is deleted (cascade)
    file_node = await create_repos.file_repo.get_by_key(file_key)
    assert file_node is None

    # Verify no projects remain
    projects = await project_service.get_all()
    assert len(projects) == 0


@pytest.mark.asyncio
async def test_cascade_delete_project_with_nested_structure(
    create_project, create_repos
):
    """Test cascade delete with a more complex nested structure."""
    project_service = ProjectService(create_repos)
    folder_service = FolderService(create_repos)
    file_service = FileService(create_repos)
    function_service = FunctionService(create_repos)
    document_service = DocumentService(create_repos)
    log_service = LogService(create_repos)

    # Create nested structure: project -> folder -> file
    folder1 = await folder_service.create(
        "Folder 1",
        "test_project.folder1",
        "First folder",
        "folder1"
    )
    folder2 = await folder_service.create(
        "Folder 2",
        "test_project.folder2",
        "Second folder",
        "folder2"
    )
    file1 = await file_service.create(
        "File 1",
        "test_project.file1",
        "First file",
        "file1",
        "hash1"
    )
    file2 = await file_service.create(
        "File 2",
        "test_project.file2",
        "Second file",
        "file2",
        "hash2"
    )

    # Create a function inside file1 for logs
    function1 = await function_service.create(
        "Test Function",
        "test_project.file1.test_function",
        "Test function description",
        CodePosition(
            line_no=1,
            col_offset=0,
            end_line_no=10,
            end_col_offset=0,
        )
    )
    await file_service.add_function(file1.id, function1.id)

    # Build structure: project -> folder1, folder2;
    # folder1 -> file1; folder2 -> file2
    await project_service.add_folder(create_project.id, folder1.id)
    await project_service.add_folder(create_project.id, folder2.id)
    await folder_service.add_file(folder1.id, file1.id)
    await folder_service.add_file(folder2.id, file2.id)

    # Create documents linked to project and file1
    doc1 = await document_service.create(
        "Project Document",
        "Document for project",
        create_project.key
    )
    doc2 = await document_service.create(
        "File Document",
        "Document for file",
        file1.key
    )

    # Create logs linked to function1
    log_params1 = RegisterLogsParams(
        function_id=function1.id,
        chain_id="test-chain-1",
        timestamp=datetime.now(timezone.utc),
        duration_ms=None,
        event_type=LogEventType.ENTER,
        message="Function entered",
        payload=None,
        result=None,
        error=None,
    )
    log1 = await log_service.create(function1.id, log_params1)

    log_params2 = RegisterLogsParams(
        function_id=function1.id,
        chain_id="test-chain-1",
        timestamp=datetime.now(timezone.utc),
        duration_ms=100.5,
        event_type=LogEventType.EXIT,
        message="Function exited",
        payload=None,
        result=None,
        error=None,
    )
    log2 = await log_service.create(function1.id, log_params2)

    # Verify structure exists
    project_children = await project_service.get_children(create_project.id)

    assert len(project_children) == 5

    folder1_children = await folder_service.get_children(folder1.id)
    assert len(folder1_children) == 2

    folder2_children = await folder_service.get_children(folder2.id)
    assert len(folder2_children) == 1

    # Verify documents exist
    project_docs = await document_service.get_nodes_by_parent_node(
        create_project.id
    )
    assert len(project_docs) == 1
    assert project_docs[0].key == doc1.key

    file_docs = await document_service.get_nodes_by_parent_node(file1.id)
    assert len(file_docs) == 1
    assert file_docs[0].key == doc2.key

    # Verify logs exist
    log1_check = await create_repos.log_repo.get_by_key(log1.key)
    assert log1_check is not None
    assert log1_check.id == log1.id

    log2_check = await create_repos.log_repo.get_by_key(log2.key)
    assert log2_check is not None
    assert log2_check.id == log2.id

    # Store keys for verification
    project_key = create_project.key
    folder1_key = folder1.key
    folder2_key = folder2.key
    file1_key = file1.key
    file2_key = file2.key
    function1_key = function1.key
    doc1_key = doc1.key
    doc2_key = doc2.key
    log1_key = log1.key
    log2_key = log2.key

    # Delete project (should cascade delete everything)
    deleted = await project_service.delete(create_project)
    assert deleted is True

    # Verify all nodes are deleted
    assert await create_repos.project_repo.get_by_key(project_key) is None
    assert await create_repos.folder_repo.get_by_key(folder1_key) is None
    assert await create_repos.folder_repo.get_by_key(folder2_key) is None
    assert await create_repos.file_repo.get_by_key(file1_key) is None
    assert await create_repos.file_repo.get_by_key(file2_key) is None
    assert await create_repos.function_repo.get_by_key(function1_key) is None

    # Verify documents are deleted
    assert await create_repos.document_repo.get_by_key(doc1_key) is None
    assert await create_repos.document_repo.get_by_key(doc2_key) is None

    # Verify logs are deleted (edges should be removed,
    # logs may remain orphaned)
    # Note: Logs are in separate collection, so they might not be deleted
    # by cascade delete unless explicitly handled
    log1_after = await create_repos.log_repo.get_by_key(log1_key)
    log2_after = await create_repos.log_repo.get_by_key(log2_key)
    # Logs might still exist but edges should be deleted
    # Since function1 is deleted, verify that log edges are also deleted
    # by checking that log_to_function edges don't exist
    if log1_after:
        # Verify log_to_function edge is deleted
        edges = await create_repos.log_to_function_edges.find(
            {"from_id": log1.id}
        )
        assert len(edges) == 0
    if log2_after:
        # Verify log_to_function edge is deleted
        edges = await create_repos.log_to_function_edges.find(
            {"from_id": log2.id}
        )
        assert len(edges) == 0
