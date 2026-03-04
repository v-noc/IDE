from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.builder.tree_builder import TreeBuilder
from app.core.services.document_service import DocumentService
import pytest

from app.core.services.file_service import FileService


@pytest.mark.asyncio
async def test_create_document(project_uow, create_sample_project, terminusdb_client):
    project = create_sample_project
    repos = Repositories(terminusdb_client)
    proj_service = ProjectService(repos)

    children = await proj_service.get_children(project.db_name)
    tree = TreeBuilder(children).build()

    document_service = DocumentService(repos, project)
    file_service = FileService(repos, project)
    created = await document_service.create("test", "test", tree[0].id)
    assert created
    assert created.name == "test"
    assert created.description == "test"
    assert created.data == ""

    node = await repos.document_repo.get_by_parent_node(tree[0].id, project.db_name)
    assert node
    assert node[0].id == created.id

    parent = await file_service.get(tree[0].id)
    assert list(parent.documents)[0] == created.id

    await document_service.delete(created.id)

    node = await file_service.get(tree[0].id)
    assert node
    assert len(node.documents) == 0
