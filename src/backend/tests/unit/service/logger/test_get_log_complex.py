from datetime import datetime, timezone, timedelta
from typing import List

from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.builder.log_tree_builder import LogTreeBuilder
from app.core.services.log_service import LogService


def _find_fn(nodes, name: str):
    for n in nodes:
        if getattr(n, 'node_type', '') == 'function' and n.name == name:
            return n
        res = _find_fn(getattr(n, 'children', []) or [], name)
        if res:
            return res
    return None


def test_multiple_chains_and_nested_logs(create_sample_project, arangodb_client):
    repos = Repositories(arangodb_client)
    proj_service = ProjectService(repos)
    project = proj_service.get_all()
    assert project

    from app.core.builder.tree_builder import TreeBuilder
    from app.core.schemas.log_tree import LogTreeNode
    from app.api.json_rpc.schemas import RegisterLogsParams, LogEventType

    children = proj_service.get_children(project[0].id)
    tree = TreeBuilder(children).build()

    factory_fn = _find_fn(tree, 'factory')
    add_fn = _find_fn(tree, 'add')
    build_fn = _find_fn(tree, 'build')
    assert factory_fn and add_fn and build_fn

    log_service = LogService(repos)

    # Chain A: factory(enter) -> add(enter, log, exit) -> build(enter, exit)
    base = datetime.now(timezone.utc)
    from app.api.json_rpc.schemas import RegisterLogsParams, LogEventType

    p_enter = RegisterLogsParams(

        chain_id="chain-A",
        timestamp=base,
        duration_ms=None,
        event_type=LogEventType.ENTER,
        message="factory enter A",
        payload=None,
        result=None,
        error=None,
    )
    parent_log_A = log_service.create(factory_fn.id, p_enter)

    a_enter = RegisterLogsParams(

        chain_id="chain-A",
        timestamp=base + timedelta(milliseconds=1),
        duration_ms=None,
        event_type=LogEventType.ENTER,
        message="add enter A",
        payload=None,
        result=None,
        error=None,
    )
    add_enter_A = log_service.create(
        add_fn.id, a_enter, parent_function_id=factory_fn.id)

    a_log = RegisterLogsParams(

        chain_id="chain-A",
        timestamp=base + timedelta(milliseconds=2),
        duration_ms=None,
        event_type=LogEventType.LOG,
        message="add log A",
        payload=None,
        result=None,
        error=None,
    )
    add_log_A = log_service.create(
        add_fn.id, a_log, parent_function_id=factory_fn.id)

    b_enter = RegisterLogsParams(

        chain_id="chain-A",
        timestamp=base + timedelta(milliseconds=3),
        duration_ms=None,
        event_type=LogEventType.ENTER,
        message="build enter A",
        payload=None,
        result=None,
        error=None,
    )
    build_enter_A = log_service.create(
        build_fn.id, b_enter, parent_function_id=add_fn.id)

    b_exit = RegisterLogsParams(
        chain_id="chain-A",
        timestamp=base + timedelta(milliseconds=4),
        duration_ms=1.2,
        event_type=LogEventType.EXIT,
        message="build exit A",
        payload=None,
        result="ok",
        error=None,
    )
    build_exit_A = log_service.create(
        build_fn.id, b_exit, parent_function_id=add_fn.id)

    a_exit = RegisterLogsParams(
        chain_id="chain-A",
        timestamp=base + timedelta(milliseconds=5),
        duration_ms=2.5,
        event_type=LogEventType.EXIT,
        message="add exit A",
        payload=None,
        result="done",
        error=None,
    )
    add_exit_A = log_service.create(
        add_fn.id, a_exit, parent_function_id=factory_fn.id)

    # Chain B: independent chain on factory only (noise)
    p_enter_B = RegisterLogsParams(
        chain_id="chain-B",
        timestamp=base,
        duration_ms=None,
        event_type=LogEventType.ENTER,
        message="factory enter B",
        payload=None,
        result=None,
        error=None,
    )
    log_service.create(factory_fn.id, p_enter_B)

    # Build log tree for Chain A starting at factory enter A
    tree_logs = log_service.get_log_containment_tree(parent_log_A.id)

    assert tree_logs, "log tree should not be empty"
    root = tree_logs[0]

    # 1. Assert factory -> add relationship (root -> add_enter_A)
    assert len(root.children) == 1
    add_enter_node = root.children[0]
    assert add_enter_node.id == add_enter_A.id

    # 2. Assert children of 'add_enter_A'
    add_children_ids = {c.id for c in add_enter_node.children}
    expected_add_children = {add_log_A.id, build_enter_A.id, add_exit_A.id}
    assert add_children_ids == expected_add_children

    # 3. Assert children of 'build_enter_A'
    build_enter_node = next(
        c for c in add_enter_node.children if c.id == build_enter_A.id)
    assert len(build_enter_node.children) == 1
    build_exit_node = build_enter_node.children[0]
    assert build_exit_node.id == build_exit_A.id


def test_get_function_log_tree(create_sample_project, arangodb_client):
    repos = Repositories(arangodb_client)
    proj_service = ProjectService(repos)
    project = proj_service.get_all()
    assert project

    from app.core.builder.tree_builder import TreeBuilder
    from app.api.json_rpc.schemas import RegisterLogsParams, LogEventType

    children = proj_service.get_children(project[0].id)
    tree = TreeBuilder(children).build()

    factory_fn = _find_fn(tree, 'factory')
    add_fn = _find_fn(tree, 'add')
    assert factory_fn and add_fn

    log_service = LogService(repos)
    base = datetime.now(timezone.utc)
    chain_id = "chain-D"

    # Log 1 for factory (a root log for this function)
    factory_enter_log = log_service.create(factory_fn.id, RegisterLogsParams(
        chain_id=chain_id, timestamp=base, event_type=LogEventType.ENTER, message="enter factory"
    ))

    # Log 2 for add, child of log 1
    add_enter_log = log_service.create(add_fn.id, RegisterLogsParams(
        chain_id=chain_id, timestamp=base + timedelta(milliseconds=1), event_type=LogEventType.LOG, message="log in add"
    ), parent_function_id=factory_fn.id)

    # Log 3 for factory, should be a child of Log 1
    factory_exit_log = log_service.create(factory_fn.id, RegisterLogsParams(
        chain_id=chain_id, timestamp=base + timedelta(milliseconds=2), event_type=LogEventType.EXIT, message="exit factory"
    ))

    # Test get_function_log for factory_fn
    factory_logs_tree = log_service.get_function_log(factory_fn.id)

    # The builder returns only root nodes. In this chain, only factory_enter is a root.
    assert len(factory_logs_tree) == 1
    root = factory_logs_tree[0]
    assert root.id == factory_enter_log.id

    # The 'exit' log should be a child of the 'enter' log from the same function.
    assert len(root.children) == 2
    child_ids = {c.id for c in root.children}
    assert child_ids == {factory_exit_log.id, add_enter_log.id}
