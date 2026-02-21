from typing import List
from datetime import datetime, timezone
import uuid

from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.builder.log_tree_builder import LogTreeBuilder
from app.core.services.log_service import LogService
import pytest

from app.core.model.logs import LogLevelName


@pytest.mark.asyncio
async def test_get_log_tree(create_sample_project, terminusdb_client):
    project = create_sample_project
    repos = Repositories(terminusdb_client)
    proj_service = ProjectService(repos)

    from app.core.builder.tree_builder import TreeBuilder
    from app.core.schemas.tree import AnyTreeNode
    from app.core.model.schemas import FunctionSchema, LogSchema
    from app.api.json_rpc.schemas import RegisterLogsParams, LogEventType

    children = await proj_service.get_children(project.db_name)
    tree = TreeBuilder(children).build()

    def find_fn(nodes: List[AnyTreeNode], name: str):
        for n in nodes:
            if n.id.startswith(FunctionSchema.__name__) and n.name == name:
                return n
            res = find_fn(getattr(n, 'children', []) or [], name)
            if res:
                return res
        return None

    factory_fn = find_fn(tree, 'factory')
    add_fn = find_fn(tree, 'add')
    assert factory_fn and add_fn

    log_service = LogService(repos, project)
    parent_params = RegisterLogsParams(
        id=str(uuid.uuid4()),
        function_id=factory_fn.id,
        chain_id="chain-tree",
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

    child_params = RegisterLogsParams(
        id=str(uuid.uuid4()),
        parent_log_id=parent_params.id,
        function_id=add_fn.id,
        chain_id="chain-tree",
        timestamp=datetime.now(timezone.utc),
        duration_ms=None,
        event_type=LogEventType.LOG,
        level_name=LogLevelName.INFO,
        message="child log",
        payload=None,
        result=None,
        error=None,
    )
    await log_service.create_batch([child_params, parent_params])

    tree_logs = await log_service.get_function_log(factory_fn.id)
    assert tree_logs and len(tree_logs[0].children) == 1
    assert tree_logs[0].children[0].id == f"{LogSchema.__name__}/{child_params.id}"
