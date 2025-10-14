from datetime import datetime, timezone
from typing import List

from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.builder.tree_builder import TreeBuilder
from app.core.services.log_service import LogService
from app.api.json_rpc.schemas import RegisterLogsParams, LogEventType


def _find_node(nodes, name: str, node_type: str):
    for n in reversed(nodes):
        if getattr(n, 'node_type', '') == node_type and n.name == name:
            return n
        res = _find_node(getattr(n, 'children', []) or [], name, node_type)
        if res:
            return res
    return None


def test_get_logs_for_call_chain(create_sample_project, arangodb_client):
    repos = Repositories(arangodb_client)
    proj_service = ProjectService(repos)
    project = proj_service.get_all()
    assert project

    children = proj_service.get_children(project[0].id)
    tree = TreeBuilder(children).build()

    # Find all the functions and calls needed for the test
    main_fn = _find_node(tree, 'main', 'function')
    factory_call_fn = _find_node(tree, 'factory_call', 'function')
    call_back_fn = _find_node(tree, 'call_back', 'function')
    factory_fn = _find_node(tree, 'factory', 'function')
    add_fn = _find_node(tree, 'add', 'function')
    build_fn = _find_node(tree, 'build', 'function')

    # This call is nested: main -> factory_call -> add -> build
    build_call = _find_node(tree, 'build', 'call')

    assert all([main_fn, factory_call_fn, factory_fn,
               add_fn, build_fn, build_call])

    log_service = LogService(repos)

    # Chain that spans the whole call chain
    log_service.create(main_fn.id, RegisterLogsParams(
        chain_id="chain-A", timestamp=datetime.now(timezone.utc), event_type=LogEventType.ENTER, message="main enter"))
    log_service.create(main_fn.id, RegisterLogsParams(
        chain_id="chain-A", timestamp=datetime.now(timezone.utc), event_type=LogEventType.LOG, message="main log"))
    log_service.create(main_fn.id, RegisterLogsParams(
        chain_id="chain-A", timestamp=datetime.now(timezone.utc), event_type=LogEventType.EXIT, message="main exit"))
    log_service.create(factory_call_fn.id, parent_function_id=main_fn.id, params=RegisterLogsParams(
        chain_id="chain-A", timestamp=datetime.now(timezone.utc),  event_type=LogEventType.ENTER, message="factory_call enter"))

    log_service.create(call_back_fn.id, parent_function_id=main_fn.id, params=RegisterLogsParams(
        chain_id="chain-A", timestamp=datetime.now(timezone.utc),  event_type=LogEventType.ENTER, message="call_back enter"))
    log_service.create(factory_fn.id, parent_function_id=main_fn.id, params=RegisterLogsParams(
        chain_id="chain-A", timestamp=datetime.now(timezone.utc),  event_type=LogEventType.ENTER, message="factory enter"))
    log_service.create(add_fn.id, parent_function_id=call_back_fn.id, params=RegisterLogsParams(
        chain_id="chain-A", timestamp=datetime.now(timezone.utc),  event_type=LogEventType.ENTER, message="add enter"))
    log_service.create(build_fn.id, parent_function_id=add_fn.id, params=RegisterLogsParams(
        chain_id="chain-A", timestamp=datetime.now(timezone.utc),  event_type=LogEventType.ENTER, message="build enter"))

    log_service.create(build_fn.id, parent_function_id=build_fn.id, params=RegisterLogsParams(
        chain_id="chain-A", timestamp=datetime.now(timezone.utc),  event_type=LogEventType.LOG, message="build log"))

    log_service.create(build_fn.id, parent_function_id=build_fn.id, params=RegisterLogsParams(
        chain_id="chain-A", timestamp=datetime.now(timezone.utc),  event_type=LogEventType.EXIT, message="build exit"))

    # Noise chain that only touches some functions
    log_service.create(main_fn.id, RegisterLogsParams(chain_id="chain-B", timestamp=datetime.now(
        timezone.utc), event_type=LogEventType.LOG, message="some other log"))
    log_service.create(build_fn.id, RegisterLogsParams(
        chain_id="chain-B", timestamp=datetime.now(timezone.utc), event_type=LogEventType.LOG, message="another log"))

    # Get logs for the call chain ending at 'build_call'
    log_tree = log_service.get_call_log(build_call.id)

    # The result should be a single tree for chain-A
    assert len(log_tree) == 1

    root = log_tree[0]
    assert root.message == "build enter"
    assert len(root.children) == 2

    # Check immediate children of main
    child_messages = {c.message for c in root.children}
    expected_child_messages = {
        "build log",
        "build exit",

    }
    assert child_messages == expected_child_messages
