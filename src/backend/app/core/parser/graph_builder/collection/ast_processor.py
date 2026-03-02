import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Union

from app.core.model.nodes import ClassNode, CodePosition, FileNode, FunctionNode
from app.core.model.schemas import (
    CallGroupSchema,
    CallSchema,
    ClassSchema,
    CodeElementGroupSchema,
    FunctionSchema,
)
from app.core.parser.ast.models import BaseNode
from app.core.parser.ast.models import ClassNode as ASTClassNode
from app.core.parser.ast.models import FunctionNode as ASTFunctionNode
from app.core.parser.jedi_adapter.resolver import MROResolver
from app.core.repository import Repositories

logger = logging.getLogger(__name__)


class ASTProcessor:
    def __init__(self, repos: Repositories, mro_resolver: Optional[MROResolver] = None):
        self.repos = repos
        self.mro_resolver = mro_resolver

    async def sync_content(
        self,
        file_node: FileNode,
        nodes: List[BaseNode],
        project_db_name: str,
        content: Optional[str] = None,
        progress_tracker=None,
    ) -> List[any]:
        """
        Synchronize AST nodes as descendants of the given file node.
        Handles Creation, Updates, and Deletions of child nodes.
        """
        # 1. Fetch existing nodes from database
        existing_map = await self._build_existing_map(file_node, project_db_name)

        # 2. Flatten AST & Prepare desired nodes
        desired_nodes_data = []
        self._flatten_nodes(
            nodes,
            file_node,
            file_node.path,
            content,
            desired_nodes_data,
            progress_tracker,
        )

        # 3. Determine what operations need to be performed
        sync_ops = self._determine_sync_operations(
            desired_nodes_data, existing_map)

        # 4. Execute batch operations
        await self._execute_batch_operations(sync_ops, file_node.path, project_db_name)

        return sync_ops["current_nodes"]

    async def _build_existing_map(
        self, file_node: FileNode, project_db_name: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build a map of existing nodes from the containment tree.
        Returns a dict mapping node_id to {"node": Node, "parent_id": str}
        """
        existing_tree = await self.repos.file_repo.get_children(
            file_node.id,
            exclude_types=[
                CallSchema.__name__,
                CodeElementGroupSchema.__name__,
                CallGroupSchema.__name__,
            ],
            project_db_name=project_db_name,
        )

        existing_map = {}
        child_to_parent = {}
        try:

            for node in existing_tree:
                for child in node.children:
                    child_to_parent.get(node.id, set()).add(child)

            for node in existing_tree:
                existing_map[node.id] = {
                    "node": node,
                    "parent_id": child_to_parent.get(node.id, None),
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error building existing map why: {e}")
            return {}

        return existing_map

    def _prepare_new_node(
        self, ast_node: BaseNode, node_data: Dict[str, Any], node_id: str
    ) -> Union[FunctionNode, ClassNode]:
        """
        Create a new node model from AST data.
        """
        position = CodePosition(
            line_no=ast_node.position.line,
            col_offset=ast_node.position.column,
            end_line_no=ast_node.position.end_line,
            end_col_offset=ast_node.position.end_column,
        )

        if node_data["type"] == "class":
            mro = node_data.get("mro", [])
            return ClassNode(
                id=f"{node_id}",
                name=ast_node.name,
                qname=node_data["qname"],
                code_position=position,
                base_classes=mro,
                description=f"Class {ast_node.name}",
            )
        else:
            return FunctionNode(
                id=f"{node_id}",
                name=ast_node.name,
                qname=node_data["qname"],
                code_position=position,
                description=f"Function {ast_node.name}",
            )

    def _update_existing_node(
        self,
        existing_node: Union[FunctionNode, ClassNode],
        new_node: Union[FunctionNode, ClassNode],
    ) -> None:
        """
        Update existing node fields with new values, preserving other fields
        like created_at, theme_config, documents, etc.
        """
        # Update fields that come from AST parsing
        existing_node.name = new_node.name
        existing_node.qname = new_node.qname
        existing_node.code_position = new_node.code_position

        # Update ClassNode-specific fields
        if isinstance(existing_node, ClassNode) and isinstance(new_node, ClassNode):
            existing_node.base_classes = new_node.base_classes

    def _determine_sync_operations(
        self,
        desired_nodes_data: List[Dict[str, Any]],
        existing_map: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Determine what nodes need to be created, updated, moved, or deleted.
        Returns a dict with keys: funcs_to_create, classes_to_create,
        funcs_to_update, classes_to_update, moves_to_execute, ids_to_delete,
        current_nodes
        """
        funcs_to_create: List[FunctionNode] = []
        classes_to_create: List[ClassNode] = []
        funcs_to_update: List[FunctionNode] = []
        classes_to_update: List[ClassNode] = []
        moves_to_execute: List[tuple[str, str]] = []  # (child_id, parent_id)
        processed_ids = set()
        current_nodes = []

        for data in desired_nodes_data:
            ast_node: BaseNode = data["node"]
            node_data: Dict[str, Any] = data["node_data"]
            parent_id: str = data["parent_id"]

            if not ast_node.id:
                continue

            node_id = ast_node.id

            processed_ids.add(node_id)

            existing_entry = existing_map.get(node_id)
            existing_node = existing_entry["node"] if existing_entry else None
            existing_parent_id = existing_entry["parent_id"] if existing_entry else None

            # Prepare new node model
            new_node = self._prepare_new_node(ast_node, node_data, node_id)
            current_nodes.append(new_node)

            if not existing_node:
                # Node doesn't exist, create it
                if isinstance(new_node, ClassNode):
                    classes_to_create.append(new_node)
                else:
                    funcs_to_create.append(new_node)

                moves_to_execute.append(
                    (
                        node_id,
                        parent_id,
                        "class" if isinstance(
                            new_node, ClassNode) else "function",
                    )
                )
                logger.debug(f"Will create new node: {new_node.qname}")
            else:
                # Node exists, check if update is needed
                needs_update = (
                    existing_node.name != new_node.name
                    or existing_node.qname != new_node.qname
                    or existing_node.code_position != new_node.code_position
                    or (
                        isinstance(existing_node, ClassNode)
                        and isinstance(new_node, ClassNode)
                        and existing_node.base_classes != new_node.base_classes
                    )
                )

                if needs_update:
                    # Update existing node fields instead of replacing
                    self._update_existing_node(existing_node, new_node)

                    if isinstance(existing_node, ClassNode):
                        classes_to_update.append(existing_node)
                    else:
                        funcs_to_update.append(existing_node)
                    logger.debug(f"Node updated: {existing_node.qname}")

                # Check if parent changed
                if existing_parent_id != parent_id:
                    logger.debug(
                        f"Node moved: {existing_node.qname} -> parent {parent_id}"
                    )
                    moves_to_execute.append(
                        (
                            node_id,
                            parent_id,
                            "class"
                            if isinstance(existing_node, ClassNode)
                            else "function",
                        )
                    )

        # Calculate nodes to delete
        ids_to_delete = [
            sid for sid in existing_map if sid not in processed_ids]

        return {
            "funcs_to_create": funcs_to_create,
            "classes_to_create": classes_to_create,
            "funcs_to_update": funcs_to_update,
            "classes_to_update": classes_to_update,
            "moves_to_execute": moves_to_execute,
            "ids_to_delete": ids_to_delete,
            "current_nodes": current_nodes,
        }

    async def _execute_batch_operations(
        self, sync_ops: Dict[str, Any], file_path: str, project_db_name: str
    ) -> None:
        """
        Execute all batch operations (create, update, move, delete).
        """
        funcs_to_create = sync_ops["funcs_to_create"]
        classes_to_create = sync_ops["classes_to_create"]
        funcs_to_update = sync_ops["funcs_to_update"]
        classes_to_update = sync_ops["classes_to_update"]
        moves_to_execute = sync_ops["moves_to_execute"]
        ids_to_delete = sync_ops["ids_to_delete"]

        # client = self.repos.client.clone()
        # await client.set_db(project_db_name)
        new_branch = f"main"

        # await client.create_branch(new_branch_id=new_branch)
        # client.branch = new_branch

        await self.repos.file_repo.flush_batch(
            funcs_to_create + classes_to_create,
            funcs_to_update + classes_to_update,
            ids_to_delete,
            moves_to_execute,
            project_db_name=project_db_name,
            branch_name=new_branch,
        )

    def _flatten_nodes(
        self,
        nodes: List[BaseNode],
        parent_node: Union[FileNode, FunctionNode, ClassNode],
        file_path: str,
        content: Optional[str],
        result_list: List[dict],
        progress_tracker=None,
    ) -> None:
        """Recursively flatten nodes and prepare their metadata."""
        for node in nodes:
            if isinstance(node, (ASTClassNode, ASTFunctionNode)):
                qname = f"{parent_node.qname}.{node.name}"
                node_type = "class" if isinstance(
                    node, ASTClassNode) else "function"

                # Track entity discovery for progress reporting
                if progress_tracker:
                    progress_tracker.increment_discovery(node_type)

                mro = []
                if isinstance(node, ASTClassNode) and self.mro_resolver and content:
                    mro = self._resolve_mro(node, file_path, content)

                node_data = {"qname": qname, "type": node_type, "mro": mro}

                result_list.append(
                    {"node": node, "node_data": node_data,
                        "parent_id": parent_node.id}
                )

                if node.id:
                    node_id = node.id
                else:
                    continue

                if node_type == "class":
                    pseudo_parent = ClassNode(
                        id=node_id,
                        name=node.name,
                        qname=qname,
                        code_position=CodePosition(
                            line_no=0, col_offset=0, end_line_no=0, end_col_offset=0
                        ),
                        base_classes=[],
                        description=f"Class {node.name}",
                    )
                else:
                    pseudo_parent = FunctionNode(
                        id=node_id,
                        name=node.name,
                        qname=qname,
                        code_position=CodePosition(
                            line_no=0, col_offset=0, end_line_no=0, end_col_offset=0
                        ),
                        description=f"Function {node.name}",
                    )

                if hasattr(node, "children"):
                    self._flatten_nodes(
                        node.children,
                        pseudo_parent,
                        file_path,
                        content,
                        result_list,
                        progress_tracker,
                    )

    def _resolve_mro(
        self, node: ASTClassNode, file_path: str, content: str
    ) -> List[str]:
        try:
            name_column = self._get_name_column(content, node)
            return self.mro_resolver.resolve_mro(
                file_path=file_path,
                source=content,
                line=node.position.line,
                column=name_column + (len(node.name)),
            )
        except Exception as e:
            logger.error(f"Failed to resolve MRO for {node.name}: {e}")
            return []

    def _get_name_column(self, content: str, node: BaseNode) -> int:
        line_index = node.position.line - 1
        if line_index < 0:
            return node.position.column
        lines = content.splitlines()
        if line_index >= len(lines):
            return node.position.column
        line = lines[line_index]
        name_idx = line.find(node.name)
        if name_idx == -1:
            return node.position.column
        return name_idx

    def _compute_checksum(self, node: BaseNode) -> str:
        data = node.model_dump(exclude={"id", "children"})
        data["children_hash"] = self._hash_children(node.children)
        encoded = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _hash_children(self, children: List[BaseNode]) -> str:
        if not children:
            return ""
        hashes = []
        for child in children:
            hashes.append(child.name + child.type + str(child.position))
        return hashlib.sha256("".join(hashes).encode("utf-8")).hexdigest()
