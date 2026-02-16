import logging
import asyncio
import aiofiles
from pathlib import Path
from typing import List, Dict, Optional

from app.core.parser.ast.models import (
    BaseNode,
    ClassNode as ASTClassNode,
    FunctionNode as ASTFunctionNode
)
from app.core.model.nodes import FileNode
from app.core.parser.ast.scanner import scan
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.repository import Repositories
from app.core.parser.graph_builder.performance import tracker

# IMPORT YOUR NEW BUILDER
from app.core.parser.graph_builder.call_graph.builder import CallChainBuilder

logger = logging.getLogger(__name__)


class BodyParser:
    def __init__(
        self,
        project_path: Path,
        project_name: str,
        repos: Repositories,
        jedi_manager: JediProjectManager,
        batch_size: int = 1000,
        progress_tracker=None,
    ):
        self.project_path = project_path
        self.repos = repos
        self.progress_tracker = progress_tracker

        # Initialize the NEW Builder here
        self.call_chain_builder = CallChainBuilder(
            project_path=project_path,
            repos=repos,
            jedi_manager=jedi_manager
        )

    async def process_ast(self, file_node: FileNode):
        """
        Phase 2: Analyze the AST tree.
        Traverses the tree, finds DB nodes, and delegates call processing to CallChainBuilder.
        """
        file_path = Path(file_node.path)
        if not file_path.is_absolute():
            file_path = Path(self.project_path) / file_path

        # 1. Prefetch DB nodes (Optimization)
        existing_tree = await self.repos.nodes.get_containment_tree(
            file_node.id,
            depth=50,
            exclude_types=["call", "group"]
        )

        node_map: Dict[str, any] = {file_node.qname: file_node}

        for item in existing_tree:

            vertex = item["vertex"]
            if vertex.get("qname"):
                # Simply storing the dict or converting to model depending on preference
                # Assuming your Builder expects Pydantic models:
                if vertex['node_type'] == 'function':
                    node_map[vertex['qname']
                             ] = self.repos.function_repo._validate(vertex)
                elif vertex['node_type'] == 'class':
                    node_map[vertex['qname']
                             ] = self.repos.class_repo._validate(vertex)

        # 2. Read Source
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as source:
                content = await source.read()
        except OSError:
            return

        # 3. Scan AST
        loop = asyncio.get_event_loop()
        try:
            nodes, processed_content = await loop.run_in_executor(
                None, scan, content, str(file_path)
            )
        except Exception:
            return

        # 4. Traverse and delegate to Builder
        await self._traverse_and_process(
            nodes,
            file_node,
            node_map,
            file_path=file_path,
            source=processed_content
        )

    async def _traverse_and_process(
        self,
        nodes: List[BaseNode],
        current_scope: any,
        node_map: Dict[str, any],
        file_path: Path,
        source: str,
    ):
        """
        Recursive traversal. When a scope (Function/Class) is found:
        1. Find its DB node.
        2. Pass it to CallChainBuilder to handle call synchronization.


        """

        # Set current function qname for non-file scopes (functions/classes)
        if current_scope.node_type in ("function", "class") and self.progress_tracker:
            self.progress_tracker.set_current_function(current_scope.qname)
            await self.progress_tracker.emit()

        await self.call_chain_builder.process_node_scope(
            node=current_scope,
            file_path=file_path,
            source_code=source,
            visited_ids=None,
        )

        # Track entity processing for non-file scopes (functions/classes)
        if current_scope.node_type in ("function", "class") and self.progress_tracker:
            self.progress_tracker.increment_entity_processed()
            # Clear current function after processing
            self.progress_tracker.clear_current_function()
            await self.progress_tracker.emit()

        for node in nodes:
            if isinstance(node, (ASTClassNode, ASTFunctionNode)):
                # 1. Identify the DB Node
                qname = f"{current_scope.qname}.{node.name}"
                db_node = node_map.get(qname)

                if not db_node:
                    continue

                # 3. Recurse for nested definitions
                if hasattr(node, "children"):
                    await self._traverse_and_process(
                        node.children,
                        db_node,
                        node_map,
                        file_path,
                        source,
                    )
