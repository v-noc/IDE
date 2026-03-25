"""Integration tests for WorkflowService using the sample project graph and a fake LLM."""

from __future__ import annotations

import pytest

from app.agent.context.graph_traversal import GraphTraversal
from app.agent.conversation_store import TerminusConversationStore
from app.agent.llm.gateway import LLMGateway
from app.agent.runner.task_manager import TaskManager
from app.agent.service.title_generator import TitleOutput
from app.agent.service.workflow_service import WorkflowService
from app.agent.workflows.description_gen import DescriptionGeneratorWorkflow
from app.agent.workflows.documentation_gen import DocumentationGeneratorWorkflow
from app.core.model.conversation_domain import TaskPart
from app.core.model.conversation_enums import TaskState
from app.core.repository.conversation import ConversationRepo
from app.db.context import ProjectUoW, RequestDbContext


# --- Fake LLM: workflow prompts (invoke) + title generator (structured output) ---


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeStructuredRunnable:
    """Feeds ``generate_conversation_title`` / ``generate_batch_conversation_title``."""

    async def ainvoke(self, messages):
        return TitleOutput(
            title="Structured Test Chat Title",
            description=(
                "One sentence describing the structured test conversation."
            ),
        )


class _FakeInnerLLM:
    def with_structured_output(self, schema):
        return _FakeStructuredRunnable()


class _FakeLLMProvider:
    def __init__(self) -> None:
        self._llm = _FakeInnerLLM()

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


class FakeAgentLLMFactory:
    """Matches ``LLMGateway.create_mini()`` and workflow ``llm_factory.create(...)``."""

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


def _workflow_params_for_main(main_node, **extra):
    return {
        "node_id": main_node.id,
        "direction": "up",
        "max_depth": 1,
        **extra,
    }


@pytest.mark.asyncio
async def test_workflow_service_run_description_workflow(
    built_sample_project,
    terminusdb_client,
):
    _, uow = built_sample_project
    graph = GraphTraversal(uow)
    llm_factory = FakeAgentLLMFactory()
    gateway = LLMGateway(llm_factory)
    workflow = DescriptionGeneratorWorkflow(
        graph=graph,
        llm_factory=llm_factory,
    )
    repo = ConversationRepo(terminusdb_client)
    store = TerminusConversationStore(repo)
    svc = WorkflowService(
        TaskManager(),
        gateway,
        db_client=terminusdb_client,
    )

    main_node = await _get_main_file_node(uow)
    conv_id, task_id = await svc.run(
        workflow,
        store=store,
        **_workflow_params_for_main(main_node),
    )
    await svc.join_task(task_id)

    meta = await store.get_conversation_metadata(conv_id)
    assert meta is not None
    assert meta.title == "Structured Test Chat Title"
    assert "structured test conversation" in meta.description.lower()

    conv = await store.get_conversation(conv_id)
    assert conv is not None
    task_parts = [
        p
        for m in conv.messages
        for p in m.parts
        if isinstance(p, TaskPart)
    ]
    assert len(task_parts) == 1
    assert task_parts[0].task_id == task_id
    assert task_id.startswith("TaskSchema/")

    task_doc = await repo.get_task(task_id)
    assert task_doc is not None
    assert task_doc.state == TaskState.COMPLETED
    assert task_doc.message_id
    assert task_doc.name.startswith("workflow:")

    sub_task = await repo.get_subtasks(task_id)

    assert len(sub_task) == 2

    repos = uow.get_project_repos()
    raw_main = await repos.client.get_document(main_node.id)

    assert raw_main["description"].startswith("DESC::")


@pytest.mark.asyncio
async def test_workflow_service_run_documentation_workflow(
    built_sample_project,
    terminusdb_client,
):
    _, uow = built_sample_project
    graph = GraphTraversal(uow)
    llm_factory = FakeAgentLLMFactory()
    gateway = LLMGateway(llm_factory)
    workflow = DocumentationGeneratorWorkflow(
        graph=graph,
        llm_factory=llm_factory,
    )
    repo = ConversationRepo(terminusdb_client)
    store = TerminusConversationStore(repo)
    svc = WorkflowService(
        TaskManager(),
        gateway,
        db_client=terminusdb_client,
    )

    main_node = await _get_main_file_node(uow)
    conv_id, task_id = await svc.run(
        workflow,
        store=store,
        **_workflow_params_for_main(main_node),
    )
    await svc.join_task(task_id)

    task_doc = await repo.get_task(task_id)
    assert task_doc is not None
    assert task_doc.state == TaskState.COMPLETED

    repos = uow.get_project_repos()
    raw_main = await repos.client.get_document(main_node.id)
    expected_doc_id = _doc_id_for_node(main_node.id)
    assert expected_doc_id in set(raw_main.get("documents", []))
    generated = await repos.client.get_document(expected_doc_id)
    assert generated["data"].startswith("DOC::")


@pytest.mark.asyncio
async def test_workflow_service_task_label_params_map_to_task_row(
    built_sample_project,
    terminusdb_client,
):
    _, uow = built_sample_project
    graph = GraphTraversal(uow)
    llm_factory = FakeAgentLLMFactory()
    gateway = LLMGateway(llm_factory)
    workflow = DescriptionGeneratorWorkflow(
        graph=graph,
        llm_factory=llm_factory,
    )
    repo = ConversationRepo(terminusdb_client)
    store = TerminusConversationStore(repo)
    svc = WorkflowService(
        TaskManager(),
        gateway,
        db_client=terminusdb_client,
    )

    main_node = await _get_main_file_node(uow)
    _, task_id = await svc.run(
        workflow,
        store=store,
        conversation_title="Custom run label",
        conversation_description="Notes for this workflow run",
        **_workflow_params_for_main(main_node),
    )
    await svc.join_task(task_id)

    task_doc = await repo.get_task(task_id)
    assert task_doc is not None
    assert task_doc.name == "Custom run label"
    assert task_doc.description == "Notes for this workflow run"


@pytest.mark.asyncio
async def test_workflow_service_batch_description_then_documentation(
    built_sample_project,
    terminusdb_client,
):
    _, uow = built_sample_project
    graph = GraphTraversal(uow)
    llm_factory = FakeAgentLLMFactory()
    gateway = LLMGateway(llm_factory)
    main_node = await _get_main_file_node(uow)
    base_params = _workflow_params_for_main(main_node)

    def workflow_factory(step: dict):
        name = step["workflow_name"]
        if name == "description_generator":
            return DescriptionGeneratorWorkflow(
                graph=graph,
                llm_factory=llm_factory,
            )
        if name == "documentation_generator":
            return DocumentationGeneratorWorkflow(
                graph=graph,
                llm_factory=llm_factory,
            )
        raise AssertionError(f"unexpected workflow {name!r}")

    repo = ConversationRepo(terminusdb_client)
    store = TerminusConversationStore(repo)
    svc = WorkflowService(
        TaskManager(),
        gateway,
        db_client=terminusdb_client,
    )

    steps = [
        {
            "workflow_name": "description_generator",
            "params": dict(base_params),
        },
        {
            "workflow_name": "documentation_generator",
            "params": dict(base_params),
        },
    ]

    conv_id, task_id = await svc.run_batch(
        steps,
        workflow_factory=workflow_factory,
        store=store,
        conversation_title="Batch parent label",
        conversation_description="Two-step batch test",
    )
    await svc.join_task(task_id)

    meta = await store.get_conversation_metadata(conv_id)
    assert meta is not None
    assert meta.title == "Structured Test Chat Title"

    task_doc = await repo.get_task(task_id)
    assert task_doc is not None
    assert task_doc.state == TaskState.COMPLETED
    assert task_doc.name == "Batch parent label"
    assert task_doc.description == "Two-step batch test"
    assert task_doc.workflow_name == "batch"

    repos = uow.get_project_repos()
    raw_main = await repos.client.get_document(main_node.id)
    assert raw_main["description"].startswith("DESC::")
    expected_doc_id = _doc_id_for_node(main_node.id)
    assert expected_doc_id in set(raw_main.get("documents", []))
