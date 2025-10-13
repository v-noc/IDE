from typing import List
from datetime import datetime, timezone

from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.builder.log_tree_builder import LogTreeBuilder
from app.core.services.log_service import LogService


def test_get_log_tree(create_sample_project, arangodb_client):
    repos = Repositories(arangodb_client)
    proj_service = ProjectService(repos)
    project = proj_service.get_all()
    assert project

    from app.core.builder.tree_builder import TreeBuilder
    from app.core.schemas.tree import AnyTreeNode
    from app.api.json_rpc.schemas import RegisterLogsParams, LogEventType

    children = proj_service.get_children(project[0].id)
    tree = TreeBuilder(children).build()

    def find_fn(nodes: List[AnyTreeNode], name: str):
        for n in nodes:
            if getattr(n, 'node_type', '') == 'function' and n.name == name:
                return n
            res = find_fn(getattr(n, 'children', []) or [], name)
            if res:
                return res
        return None

    factory_fn = find_fn(tree, 'factory')
    add_fn = find_fn(tree, 'add')
    assert factory_fn and add_fn

    log_service = LogService(repos)
    parent_params = RegisterLogsParams(
        function_id=factory_fn.id,
        chain_id="chain-tree",
        timestamp=datetime.now(timezone.utc),
        duration_ms=None,
        event_type=LogEventType.ENTER,
        message="parent enter",
        payload=None,
        result=None,
        error=None,
    )
    parent_log = log_service.create(factory_fn.id, parent_params)

    child_params = RegisterLogsParams(
        function_id=add_fn.id,
        chain_id="chain-tree",
        timestamp=datetime.now(timezone.utc),
        duration_ms=None,
        event_type=LogEventType.LOG,
        message="child log",
        payload=None,
        result=None,
        error=None,
    )
    child_log = log_service.create(
        add_fn.id, child_params, parent_function_id=factory_fn.id)

    tree_logs = log_service.get_log_containment_tree(parent_log.id)
    assert tree_logs and len(tree_logs[0].children) == 1
    assert tree_logs[0].children[0].id == child_log.id
