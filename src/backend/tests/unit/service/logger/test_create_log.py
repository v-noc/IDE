from datetime import datetime, timezone

from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.services.function_service import FunctionService
from app.core.services.log_service import LogService
from app.core.builder.tree_builder import TreeBuilder


def _find_function_by_name(tree_nodes, name: str):
    for node in tree_nodes:
        if getattr(node, 'node_type', '') == 'function' and node.name == name:
            return node
        # search children
        child = _find_function_by_name(
            getattr(node, 'children', []) or [], name)
        if child:
            return child
    return None


def _build_tree_and_get_functions(repos: Repositories):
    proj_service = ProjectService(repos)
    projects = proj_service.get_all()
    assert projects, "No project built in fixture"
    children = proj_service.get_children(projects[0].id)
    tree = TreeBuilder(children).build()
    return tree


def test_create_log_without_parent(create_sample_project, arangodb_client):
    repos = Repositories(arangodb_client)
    tree = _build_tree_and_get_functions(repos)

    # Use 'factory' function from sample project
    factory_fn = _find_function_by_name(tree, 'factory')
    assert factory_fn is not None

    service = LogService(repos)
    from app.api.json_rpc.schemas import RegisterLogsParams, LogEventType

    params = RegisterLogsParams(
        function_id=factory_fn.id,
        chain_id="chain-1",
        timestamp=datetime.now(timezone.utc),
        duration_ms=None,
        event_type=LogEventType.LOG,
        message="a log",
        payload=None,
        result=None,
        error=None,
    )

    created = service.create(factory_fn.id, params, parent_function_id=None)
    assert created is not None

    parent = service.get_parent_log(created.id)
    assert parent is None


def test_create_log_with_parent(create_sample_project, arangodb_client):
    repos = Repositories(arangodb_client)
    tree = _build_tree_and_get_functions(repos)

    factory_fn = _find_function_by_name(tree, 'factory')
    add_fn = _find_function_by_name(tree, 'add')
    assert factory_fn is not None and add_fn is not None

    service = LogService(repos)
    from app.api.json_rpc.schemas import RegisterLogsParams, LogEventType

    # Create parent ENTER log on parent function
    parent_params = RegisterLogsParams(
        function_id=factory_fn.id,
        chain_id="chain-2",
        timestamp=datetime.now(timezone.utc),
        duration_ms=None,
        event_type=LogEventType.ENTER,
        message="parent enter",
        payload=None,
        result=None,
        error=None,
    )
    parent_log = service.create(
        factory_fn.id, parent_params, parent_function_id=None)
    assert parent_log is not None

    # Create child log on child function with same chain, passing parent_function_id
    child_params = RegisterLogsParams(
        function_id=add_fn.id,
        chain_id="chain-2",
        timestamp=datetime.now(timezone.utc),
        duration_ms=None,
        event_type=LogEventType.LOG,
        message="child log",
        payload=None,
        result=None,
        error=None,
    )
    child_log = service.create(
        add_fn.id, child_params, parent_function_id=factory_fn.id)
    assert child_log is not None

    parent_from_service = service.get_parent_log(child_log.id)
    assert parent_from_service is not None
    assert parent_from_service.id == parent_log.id
