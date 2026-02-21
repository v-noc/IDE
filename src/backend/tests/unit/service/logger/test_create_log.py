from datetime import datetime, timezone
import uuid
import pytest
from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.services.function_service import FunctionService
from app.core.services.log_service import LogService
from app.core.builder.tree_builder import TreeBuilder
from app.core.model.nodes import ProjectNode
from app.core.model.schemas import FunctionSchema, LogSchema
from app.api.json_rpc.schemas import RegisterLogsParams, LogEventType, LogLevelName


def _find_function_by_name(tree_nodes, name: str):
    for node in tree_nodes:
        if node.id.startswith(FunctionSchema.__name__) and node.name == name:
            return node
        # search children
        child = _find_function_by_name(
            getattr(node, 'children', []) or [], name)
        if child:
            return child
    return None


async def _build_tree_and_get_functions(repos: Repositories, project: ProjectNode):
    proj_service = ProjectService(repos)
    children = await proj_service.get_children(project.db_name)
    tree = TreeBuilder(children).build()
    return tree


@pytest.mark.asyncio
async def test_create_log_without_parent(create_sample_project, terminusdb_client):
    project = create_sample_project
    repos = Repositories(terminusdb_client)
    tree = await _build_tree_and_get_functions(repos, project)

    # Use 'factory' function from sample project
    factory_fn = _find_function_by_name(tree, 'factory')
    assert factory_fn is not None

    service = LogService(repos, project)

    params = RegisterLogsParams(
        id=str(uuid.uuid4()),
        function_id=factory_fn.id,
        chain_id="chain-1",
        timestamp=datetime.now(timezone.utc),
        duration_ms=None,
        level_name=LogLevelName.INFO,
        event_type=LogEventType.LOG,
        message="a log",
        payload=None,
        result=None,
        error=None,
    )

    await service.create_batch([params])
    created = await service.get_function_log(factory_fn.id)
    assert created is not None

    # parent = await service.get_parent_log(created.id)
    # assert parent is None


@pytest.mark.asyncio
async def test_create_log_with_parent(create_sample_project, terminusdb_client):
    project = create_sample_project
    repos = Repositories(terminusdb_client)
    tree = await _build_tree_and_get_functions(repos, project)

    factory_fn = _find_function_by_name(tree, 'factory')
    add_fn = _find_function_by_name(tree, 'add')
    assert factory_fn is not None and add_fn is not None

    service = LogService(repos, project)

    # Create parent ENTER log on parent function
    parent_params = RegisterLogsParams(
        id=str(uuid.uuid4()),
        function_id=factory_fn.id,
        chain_id="chain-2",
        timestamp=datetime.now(timezone.utc),
        duration_ms=None,
        parent_log_id=None,
        event_type=LogEventType.ENTER,
        level_name=LogLevelName.INFO,
        message="parent enter",
        payload=None,
        result=None,
        error=None,
    )

    # Create child log on child function with same chain, passing parent_function_id
    child_params = RegisterLogsParams(
        id=str(uuid.uuid4()),
        chain_id="chain-2",
        parent_log_id=parent_params.id,
        function_id=add_fn.id,
        timestamp=datetime.now(timezone.utc),
        duration_ms=None,
        event_type=LogEventType.LOG,
        level_name=LogLevelName.INFO,
        message="child log",
        payload=None,
        result=None,
        error=None,
    )

    await service.create_batch([child_params, parent_params])

    parent_from_service = await service.get_parent_log(f"{LogSchema.__name__}/{child_params.id}")

    assert parent_from_service is not None
    assert parent_from_service.id == f"{LogSchema.__name__}/{parent_params.id}"
