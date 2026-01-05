from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.builder.tree_builder import TreeBuilder
from app.core.services.document_service import DocumentService
import pytest


@pytest.mark.asyncio
async def test_create_document(create_sample_project, arangodb_client):
    repos = Repositories(arangodb_client)
    proj_service = ProjectService(repos)
    project = await proj_service.get_all()
    assert project

    children = await proj_service.get_children(project[0].id)
    tree = TreeBuilder(children).build()

    document_service = DocumentService(repos)
    created = await document_service.create("test", "test", tree[0].key)
    assert created
    assert created.name == "test"
    assert created.description == "test"
    assert created.data == ""

    node = await repos.nodes.get_by_key(tree[0].key)
    assert node
    assert node.documents[0] == created.id

    documents = await document_service.get_nodes_by_parent_node(tree[0].key)
    assert documents
    assert len(documents) == 1
    assert documents[0].id == created.id
    assert documents[0].name == "test"
    assert documents[0].description == "test"
    assert documents[0].data == ""

    await document_service.delete(created.key, tree[0].key)

    node = await repos.nodes.get_by_key(tree[0].key)
    assert node
    assert len(node.documents) == 0
