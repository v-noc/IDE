import logging
import asyncio
import aiofiles
import uuid
from pathlib import Path
from typing import List, Optional, Dict

from app.core.parser.ast.models import (
    BaseNode,
    CallNode as ASTCallNode,
    ClassNode as ASTClassNode,
    FunctionNode as ASTFunctionNode
)
from app.core.model.nodes import FileNode, FunctionNode, ClassNode, CallNode, ContainerNode
from app.core.parser.ast.scanner import scan
from app.core.parser.graph_builder.analysis.call_chain_builder import CallChainBuilder
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.repository import Repositories
from app.core.parser.graph_builder.performance import tracker

logger = logging.getLogger(__name__)


class BodyParser:
    def __init__(
        self,
        project_path: Path,
        project_name: str,
        repos: Repositories,
        jedi_manager: JediProjectManager,
        batch_size: int = 1000,
        call_resolve_concurrency: int = 8,
    ):
        self.project_path = project_path
        self.project_name = project_name
        self.repos = repos
        self.jedi_manager = jedi_manager
        self.batch_size = batch_size
        self.call_resolve_concurrency = call_resolve_concurrency
        self.processed_scope_ids = set()

        self.call_chain_builder = CallChainBuilder(
            project_path=project_path,
            project_name=project_name,
            repos=repos,
            jedi_manager=jedi_manager,
        )

    async def process_ast(self, file_node: FileNode):
        """
        Phase 2: Analyze the AST tree for calls.
        Traverses the tree, entering scopes (Function/Class) as encountered.
        """
        with tracker.timer("body_parser.process_ast_total"):
            file_path = Path(file_node.path)
            if not file_path.is_absolute():
                file_path = Path(self.project_path) / file_path

            # Prefetch all function/class nodes for this file
            # This allows us to map AST nodes to DB IDs
            with tracker.timer("body_parser.prefetch_nodes"):
                existing_tree = await self.repos.nodes.get_containment_tree(
                    file_node.id,
                    depth=50,
                    exclude_types=["call"]
                )

                # Map qname -> DB Node
                node_map: Dict[str, ContainerNode] = {}
                for item in existing_tree:
                    vertex = item["vertex"]
                    qname = vertex.get("qname")
                    if qname:
                        # Convert to model
                        node_type = vertex.get("node_type")
                        if node_type == "function":
                            node_map[qname] = FunctionNode(**vertex)
                        elif node_type == "class":
                            node_map[qname] = ClassNode(**vertex)
                        elif node_type == "file":
                            node_map[qname] = FileNode(**vertex)

            try:
                with tracker.timer("body_parser.read_file"):
                    async with aiofiles.open(file_path, "r", encoding="utf-8") as source:
                        content = await source.read()
            except OSError as exc:
                logger.error("Failed to read file %s: %s", file_path, exc)
                return

            loop = asyncio.get_event_loop()
            try:
                # Keep processed_content: it matches node positions after ID injection.
                with tracker.timer("body_parser.scan_ast"):
                    nodes, processed_content = await loop.run_in_executor(
                        None, scan, content, str(file_path)
                    )
            except Exception as exc:
                logger.error("Failed to re-scan AST for %s: %s",
                             file_path, exc)
                return

            # Start traversal from file scope
            with tracker.timer("body_parser.traverse_ast_root"):
                await self._traverse(
                    nodes,
                    file_node,
                    node_map,
                    file_path=file_path,
                    source=processed_content,
                )
            self.processed_scope_ids.add(file_node.id)

    async def _traverse(
        self,
        nodes: List[BaseNode],
        current_node: ContainerNode,
        node_map: Dict[str, ContainerNode],
        *,
        file_path: Path,
        source: str,
    ):
        """
        Traverse AST nodes in the current scope.
        Definitions are processed sequentially.
        Calls are resolved in parallel.
        """
        call_nodes: List[ASTCallNode] = []

        for node in nodes:
            if isinstance(node, (ASTClassNode, ASTFunctionNode)):
                # Calculate qname to find DB node
                qname = f"{current_node.qname}.{node.name}"
                db_node = node_map.get(qname)

                if not db_node:
                    continue

                if hasattr(node, "children"):
                    await self._traverse(
                        node.children, db_node, node_map,
                        file_path=file_path, source=source,
                    )
                self.processed_scope_ids.add(db_node.id)

            elif isinstance(node, ASTCallNode):
                # Ensure we are inside a function or class to attach the call
                if current_node.node_type in ("function", "class"):
                    call_nodes.append(node)

        # Resolve calls in parallel
        if call_nodes:
            loop = asyncio.get_event_loop()

            async def _resolve(n: ASTCallNode):
                return n, await loop.run_in_executor(
                    None,
                    self.call_chain_builder.call_resolver.resolve_call,
                    str(file_path), source, n.position.line, n.call_col_pos, None,
                )

            resolved = await asyncio.gather(*[_resolve(n) for n in call_nodes])

            for n, resolutions in resolved:
                await self.call_chain_builder.build_chain_from_resolutions(
                    call_node=n,
                    caller_node=current_node,
                    resolutions=resolutions,
                    depth=0,
                    parent_context=None,
                )
