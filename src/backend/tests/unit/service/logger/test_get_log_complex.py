import uuid
from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from app.api.json_rpc.schemas import LogEventType, LogLevelName, RegisterLogsParams
from app.core.builder.tree_builder import TreeBuilder
from app.core.model.schemas import FunctionSchema, LogSchema
from app.core.repository import Repositories
from app.core.schemas.log_tree import LogTreeNode
from app.core.services.log_service import LogService
from app.core.services.project_service import ProjectService


def _find_function_by_name(nodes, name: str):
    for n in nodes:
        if n.id.startswith(FunctionSchema.__name__) and n.name == name:
            return n
        res = _find_function_by_name(getattr(n, "children", []) or [], name)
        if res:
            return res
    return None


@pytest.mark.asyncio
async def test_multiple_chains_and_nested_logs(
    create_sample_project, terminusdb_client
):
    project = create_sample_project
    repos = Repositories(terminusdb_client)
    proj_service = ProjectService(repos)

    children = await proj_service.get_children(project.db_name)
    tree = TreeBuilder(children).build()

    factory_fn = _find_function_by_name(tree, "factory")
    add_fn = _find_function_by_name(tree, "add")
    build_fn = _find_function_by_name(tree, "build")
    assert factory_fn and add_fn and build_fn

    log_service = LogService(repos, project)

    # Chain A: factory(enter) -> add(enter, log, exit) -> build(enter, exit)
    base = datetime.now(timezone.utc)

    p_enter = RegisterLogsParams(
        id=str(uuid.uuid4()),
        chain_id="chain-A",
        timestamp=base,
        duration_ms=None,
        event_type=LogEventType.ENTER,
        level_name=LogLevelName.INFO,
        message="factory enter A",
        function_id=factory_fn.id,
        payload=None,
        result=None,
        error=None,
    )
    # parent_log_A = log_service.create(factory_fn.id, p_enter)

    a_enter = RegisterLogsParams(
        id=str(uuid.uuid4()),
        chain_id="chain-A",
        timestamp=base + timedelta(milliseconds=1),
        duration_ms=None,
        event_type=LogEventType.ENTER,
        level_name=LogLevelName.INFO,
        function_id=add_fn.id,
        parent_log_id=p_enter.id,
        message="add enter A",
        payload=None,
        result=None,
        error=None,
    )

    a_log = RegisterLogsParams(
        id=str(uuid.uuid4()),
        chain_id="chain-A",
        timestamp=base + timedelta(milliseconds=2),
        duration_ms=None,
        parent_log_id=a_enter.id,
        event_type=LogEventType.LOG,
        level_name=LogLevelName.INFO,
        function_id=add_fn.id,
        message="add log A",
        payload=None,
        result=None,
        error=None,
    )

    b_enter = RegisterLogsParams(
        id=str(uuid.uuid4()),
        chain_id="chain-A",
        timestamp=base + timedelta(milliseconds=3),
        duration_ms=None,
        event_type=LogEventType.ENTER,
        level_name=LogLevelName.INFO,
        parent_log_id=a_enter.id,
        function_id=build_fn.id,
        message="build enter A",
        payload=None,
        result=None,
        error=None,
    )
    # build_enter_A = log_service.create(
    #     build_fn.id, b_enter, parent_function_id=add_fn.id)

    b_exit = RegisterLogsParams(
        id=str(uuid.uuid4()),
        chain_id="chain-A",
        timestamp=base + timedelta(milliseconds=4),
        duration_ms=1.2,
        parent_log_id=b_enter.id,
        event_type=LogEventType.EXIT,
        level_name=LogLevelName.INFO,
        function_id=build_fn.id,
        message="build exit A",
        payload=None,
        result="ok",
        error=None,
    )
    # build_exit_A = log_service.create(
    #     build_fn.id, b_exit, parent_function_id=add_fn.id)

    a_exit = RegisterLogsParams(
        id=str(uuid.uuid4()),
        parent_log_id=a_enter.id,
        chain_id="chain-A",
        timestamp=base + timedelta(milliseconds=5),
        duration_ms=2.5,
        event_type=LogEventType.EXIT,
        level_name=LogLevelName.INFO,
        function_id=add_fn.id,
        message="add exit A",
        payload=None,
        result="done",
        error=None,
    )

    # Chain B: independent chain on factory only (noise)
    p_enter_B = RegisterLogsParams(
        id=str(uuid.uuid4()),
        chain_id="chain-B",
        timestamp=base,
        duration_ms=None,
        event_type=LogEventType.ENTER,
        level_name=LogLevelName.INFO,
        function_id=factory_fn.id,
        message="factory enter B",
        payload=None,
        result=None,
        error=None,
    )
    # log_service.create(factory_fn.id, p_enter_B)
    await log_service.create_batch(
        [a_enter, a_log, b_enter, b_exit, a_exit, p_enter_B, p_enter]
    )

    # Build log tree for Chain A starting at factory enter A
    tree_logs = await log_service.get_function_log(factory_fn.id)

    assert tree_logs, "log tree should not be empty"
    root = None
    for log in tree_logs:
        if log.chain_id == "chain-A":
            root = log
            break
    assert root, "root log should not be empty"

    # 1. Assert factory -> add relationship (root -> add_enter_A)
    assert len(tree_logs) == 2
    add_enter_node = root.children[0]
    assert add_enter_node.id == f"{LogSchema.__name__}/{a_enter.id}"

    # 2. Assert children of 'add_enter_A'
    add_children_ids = {c.id for c in add_enter_node.children}
    expected_add_children = {f"{LogSchema.__name__}/{a_log.id}",
                             f"{LogSchema.__name__}/{b_enter.id}", f"{LogSchema.__name__}/{a_exit.id}"}
    assert add_children_ids == expected_add_children

    # 3. Assert children of 'build_enter_A'
    build_enter_node = next(
        c for c in add_enter_node.children if c.id == f"{LogSchema.__name__}/{b_enter.id}"
    )
    assert len(build_enter_node.children) == 1
    build_exit_node = build_enter_node.children[0]
    assert build_exit_node.id == f"{LogSchema.__name__}/{b_exit.id}"


@pytest.mark.asyncio
async def test_get_function_log_tree(create_sample_project, terminusdb_client):
    project = create_sample_project
    repos = Repositories(terminusdb_client)
    proj_service = ProjectService(repos)

    children = await proj_service.get_children(project.db_name)
    tree = TreeBuilder(children).build()

    factory_fn = _find_function_by_name(tree, "factory")
    add_fn = _find_function_by_name(tree, "add")
    assert factory_fn and add_fn

    log_service = LogService(repos, project)
    base = datetime.now(timezone.utc)
    chain_id = "chain-D"

    # Log 1 for factory (a root log for this function)

    factory_enter_log = RegisterLogsParams(
        id=str(uuid.uuid4()),
        chain_id=chain_id,
        parent_log_id=None,
        function_id=factory_fn.id,
        level_name=LogLevelName.INFO,
        timestamp=base,
        event_type=LogEventType.ENTER,
        message="enter factory",
        payload=None,
        result=None,
        error=None,
    )

    # Log 2 for add, child of log 1
    add_enter_log = RegisterLogsParams(
        id=str(uuid.uuid4()),
        chain_id=chain_id,
        timestamp=base + timedelta(milliseconds=1),
        event_type=LogEventType.LOG,
        level_name=LogLevelName.INFO,
        function_id=add_fn.id,
        parent_log_id=factory_enter_log.id,
        message="log in add",
        payload=None,
        result=None,
        error=None,
    )

    # Log 3 for factory, should be a child of Log 1
    factory_exit_log = RegisterLogsParams(
        id=str(uuid.uuid4()),
        chain_id=chain_id,
        timestamp=base + timedelta(milliseconds=2),
        event_type=LogEventType.EXIT,
        level_name=LogLevelName.INFO,
        function_id=factory_fn.id,
        parent_log_id=factory_enter_log.id,
        message="exit factory",
        payload=None,
        result=None,
        error=None,
    )
    await log_service.create_batch([factory_enter_log, add_enter_log, factory_exit_log])

    # Test get_function_log for factory_fn
    factory_logs_tree = await log_service.get_function_log(factory_fn.id)

    # The builder returns only root nodes. In this chain, only factory_enter is a root.
    assert len(factory_logs_tree) == 1
    root = factory_logs_tree[0]
    assert root.id == f"{LogSchema.__name__}/{factory_enter_log.id}"

    # The 'exit' log should be a child of the 'enter' log from the same function.
    assert len(root.children) == 2
    child_ids = {c.id for c in root.children}
    assert child_ids == {f"{LogSchema.__name__}/{factory_exit_log.id}",
                         f"{LogSchema.__name__}/{add_enter_log.id}"}
