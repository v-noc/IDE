import logging
from pathlib import Path
from typing import Any, List

from app.core.model.nodes import ProjectNode
from app.core.repository import Repositories
from app.core.parser.drivers import DriverManager
from app.core.parser.graph_builder.call_graph.models import ScopeSyncResult
from app.core.parser.jedi_adapter.call_resolver.call_resolver import CallFrameStack
from app.core.builder.tree_builder import TreeBuilder


from .diff_calulator import DiffCalculator

logger = logging.getLogger(__name__)


class CallChainBuilder:
    def __init__(
        self,
        project_node: ProjectNode,
        repos: Repositories,
        driver_manager: DriverManager,
        max_depth: int = 10
    ):
        self.project_node = project_node
        self.project_path = Path(project_node.path)
        self.repos = repos
        self.driver_manager = driver_manager

        self.diff_calculator = DiffCalculator()

        self.max_depth = max_depth

    async def resolve_call_hierarchy(self, file_path: Path, node: any, calls: List[Any]) -> ScopeSyncResult:

        merged_stack = CallFrameStack(
            target_qname="root", target_id="root", children=[])

        if calls:
            try:
                driver = await self.driver_manager.get_driver(str(file_path))
                result = await driver.resolve_calls(str(file_path), calls)
                merged_stack = result.call_frame_stack
            except Exception:
                logger.exception(
                    "Call hierarchy resolution failed in %s", file_path
                )

        old_children = await self.repos.call_repo.get_children(node.id, [])

        results = await self.preprocess_call_hierarchy(merged_stack, old_children, node.id)

        return results

    async def preprocess_call_hierarchy(
        self,
        call_frame_stack: CallFrameStack,
        old_children: List[Any],
        root_parent_id: str,
    ) -> ScopeSyncResult:
        old_tree = TreeBuilder(old_children).build()

        return self.diff_calculator.calculate_diff(
            root_parent_id=root_parent_id,
            new_tree=call_frame_stack,
            old_tree=old_tree,
        )
