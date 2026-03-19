import pytest

from app.agent.context.graph_traversal import GraphTraversal
from app.agent.workflows.description_gen import DescriptionGeneratorWorkflow
from app.agent.workflows.documentation_gen import (
    DocumentationGeneratorWorkflow,
)
from app.db.context import ProjectUoW, RequestDbContext


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeLLMProvider:
    async def invoke(self, messages, **kwargs):
        prompt = messages[-1].content if messages else ""
        node_name = "unknown"
        for line in prompt.splitlines():
            if line.startswith("Node name: "):
                node_name = line.replace("Node name: ", "").strip()
                break

        if "Task: documentation" in prompt:
            return _FakeResponse(f"DOC::{node_name}")
        return _FakeResponse(f"DESC::{node_name}")


class _FakeLLMFactory:
    def create(self, **kwargs):
        return _FakeLLMProvider()


def _doc_id_for_node(node_id: str) -> str:
    safe = node_id.replace("/", "_").replace(":", "_")
    return f"DocumentSchema/{safe}_workflow_documentation"


async def _get_main_file_node(uow: ProjectUoW):
    repos = uow.get_project_repos()
    file_nodes = await repos.structure_repo.get_by_qnames(
        ["sample_project.main"],
        "FileSchema",
    )
    return file_nodes["sample_project.main"]


@pytest.mark.asyncio
async def test_description_workflow_updates_node_descriptions(
    built_sample_project,
    terminusdb_client,
):
    project_node, _ = built_sample_project
    uow = ProjectUoW(terminusdb_client, project_node, RequestDbContext())
    graph = GraphTraversal(uow)
    workflow = DescriptionGeneratorWorkflow(
        graph=graph,
        llm_factory=_FakeLLMFactory(),
    )

    main_node = await _get_main_file_node(uow)
    result = await workflow.run(node_id=main_node.id, direction="up", max_depth=1)
    assert result["processed"] > 0

    repos = uow.get_project_repos()
    raw_main_doc = await repos.client.get_document(main_node.id)
    assert raw_main_doc["description"].startswith("DESC::")


@pytest.mark.asyncio
async def test_documentation_workflow_creates_documents_and_links(
    built_sample_project,
    terminusdb_client,
):
    project_node, _ = built_sample_project
    uow = ProjectUoW(terminusdb_client, project_node, RequestDbContext())
    graph = GraphTraversal(uow)
    workflow = DocumentationGeneratorWorkflow(
        graph=graph,
        llm_factory=_FakeLLMFactory(),
    )

    main_node = await _get_main_file_node(uow)
    result = await workflow.run(node_id=main_node.id, direction="up", max_depth=1)
    assert result["processed"] > 0
    assert len(result["upserted_document_ids"]) > 0

    repos = uow.get_project_repos()
    raw_main_doc = await repos.client.get_document(main_node.id)

    expected_doc_id = _doc_id_for_node(main_node.id)
    assert expected_doc_id in set(raw_main_doc.get("documents", []))
    generated_doc = await repos.client.get_document(expected_doc_id)
    assert generated_doc["data"].startswith("DOC::")


@pytest.mark.asyncio
async def test_combined_description_then_documentation_flow(
    built_sample_project,
    terminusdb_client,
):
    project_node, _ = built_sample_project
    uow = ProjectUoW(terminusdb_client, project_node, RequestDbContext())
    graph = GraphTraversal(uow)
    desc_workflow = DescriptionGeneratorWorkflow(
        graph=graph,
        llm_factory=_FakeLLMFactory(),
    )
    doc_workflow = DocumentationGeneratorWorkflow(
        graph=graph,
        llm_factory=_FakeLLMFactory(),
    )

    main_node = await _get_main_file_node(uow)
    desc_result = await desc_workflow.run(
        node_id=main_node.id,
        direction="up",
        max_depth=1,
    )
    doc_result = await doc_workflow.run(
        node_id=main_node.id,
        direction="up",
        max_depth=1,
    )

    assert desc_result["processed"] > 0
    assert doc_result["processed"] > 0

    repos = uow.get_project_repos()
    raw_main_doc = await repos.client.get_document(main_node.id)
    expected_doc_id = _doc_id_for_node(main_node.id)

    assert raw_main_doc["description"].startswith("DESC::")
    assert expected_doc_id in set(raw_main_doc.get("documents", []))
