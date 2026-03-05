from datetime import datetime, timezone
from typing import List
import uuid
import pytest
import pytest_asyncio
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


def _log_params(
    log_id: str,
    function_id: str,
    chain_id: str,
    event_type: LogEventType,
    message: str,
    parent_log_id: str | None = None,
) -> RegisterLogsParams:
    return RegisterLogsParams(
        id=log_id,
        function_id=function_id,
        chain_id=chain_id,
        timestamp=datetime.now(timezone.utc),
        event_type=event_type,
        message=message,
        parent_log_id=parent_log_id,
    )


@pytest.mark.skip(reason="Might not be needed")
@pytest.mark.asyncio
async def test_get_logs_for_call_chain(create_sample_project):
    project, project_uow = create_sample_project
    proj_service = ProjectService(project_uow)

    children = await proj_service.get_children()
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

    log_service = LogService(project_uow)

    # Build log hierarchy for chain-A: main enter -> ... -> build enter -> build log/exit
    main_enter_id = str(uuid.uuid4())
    main_log_id = str(uuid.uuid4())
    main_exit_id = str(uuid.uuid4())
    factory_call_enter_id = str(uuid.uuid4())
    call_back_enter_id = str(uuid.uuid4())
    factory_enter_id = str(uuid.uuid4())
    add_enter_id = str(uuid.uuid4())
    build_enter_id = str(uuid.uuid4())
    build_log_id = str(uuid.uuid4())
    build_exit_id = str(uuid.uuid4())

    batch_params: List[RegisterLogsParams] = [
        _log_params(main_enter_id, main_fn.id, "chain-A",
                    LogEventType.ENTER, "main enter"),
        _log_params(main_log_id, main_fn.id, "chain-A",
                    LogEventType.LOG, "main log", main_enter_id),
        _log_params(main_exit_id, main_fn.id, "chain-A",
                    LogEventType.EXIT, "main exit", main_enter_id),
        _log_params(factory_call_enter_id, factory_call_fn.id, "chain-A",
                    LogEventType.ENTER, "factory_call enter", main_enter_id),
        _log_params(call_back_enter_id, call_back_fn.id, "chain-A",
                    LogEventType.ENTER, "call_back enter", main_enter_id),
        _log_params(factory_enter_id, factory_fn.id, "chain-A",
                    LogEventType.ENTER, "factory enter", main_enter_id),
        _log_params(add_enter_id, add_fn.id, "chain-A",
                    LogEventType.ENTER, "add enter", call_back_enter_id),
        _log_params(build_enter_id, build_fn.id, "chain-A",
                    LogEventType.ENTER, "build enter", add_enter_id),
        _log_params(build_log_id, build_fn.id, "chain-A",
                    LogEventType.LOG, "build log", build_enter_id),
        _log_params(build_exit_id, build_fn.id, "chain-A",
                    LogEventType.EXIT, "build exit", build_enter_id),
        # Noise chain that only touches some functions
        _log_params(str(uuid.uuid4()), main_fn.id, "chain-B",
                    LogEventType.LOG, "some other log"),
        _log_params(str(uuid.uuid4()), build_fn.id, "chain-B",
                    LogEventType.LOG, "another log"),
    ]

    await log_service.create_batch(batch_params)

    # Get logs for the call chain ending at 'build_call'
    log_tree = await log_service.get_call_log(build_fn.id)

    # The result should be a single tree for chain-A
    assert len(log_tree) == 1

    root = log_tree[0]
    assert root.message == "build enter"
    assert len(root.children) == 2

    # Check immediate children of build enter
    child_messages = {c.message for c in root.children}
    expected_child_messages = {
        "build log",
        "build exit",
    }
    assert child_messages == expected_child_messages
