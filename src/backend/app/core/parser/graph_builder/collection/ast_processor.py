import logging
import hashlib
import json
from typing import List, Optional, Dict, Any, Union

from app.core.repository import Repositories
from app.core.model.nodes import (
    FileNode, FunctionNode, ClassNode, CodePosition, ContainerNode
)
from app.core.parser.ast.models import (
    BaseNode,
    ClassNode as ASTClassNode,
    FunctionNode as ASTFunctionNode
)
from app.core.parser.jedi_adapter.resolver import MROResolver

logger = logging.getLogger(__name__)


class ASTProcessor:
    def __init__(
        self, repos: Repositories, mro_resolver: Optional[MROResolver] = None
    ):
        self.repos = repos
        self.mro_resolver = mro_resolver

    async def sync_content(
        self,
        file_node: FileNode,
        nodes: List[BaseNode],
        content: Optional[str] = None
    ) -> List[ContainerNode]:
        """
        Synchronize AST nodes as descendants of the given file node.
        Handles Creation, Updates, and Deletions of child nodes.
        """
        # 1. Fetch existing nodes from database
        existing_map = await self._build_existing_map(file_node)

        # 2. Flatten AST & Prepare desired nodes
        desired_nodes_data = []
        self._flatten_nodes(
            nodes, file_node, file_node.path, content, desired_nodes_data
        )

        # 3. Determine what operations need to be performed
        sync_ops = self._determine_sync_operations(
            desired_nodes_data, existing_map
        )

        # 4. Execute batch operations
        await self._execute_batch_operations(sync_ops, file_node.path)

        return sync_ops["current_nodes"]

    async def _build_existing_map(
        self, file_node: FileNode
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build a map of existing nodes from the containment tree.
        Returns a dict mapping node_id to {"node": Node, "parent_id": str}
        """
        existing_tree = await self.repos.nodes.get_containment_tree(
            file_node.id,
            depth=50,
            exclude_types=["call", "group"],
        )

        existing_map = {}

        for item in existing_tree:
            vertex = item["vertex"]
            node_type = vertex.get("node_type")
            if node_type == "function":
                try:
                    node = FunctionNode(**vertex)
                except Exception as e:
                    logger.warning(f"Failed to parse FunctionNode: {e}")
                    continue
            elif node_type == "class":
                try:
                    node = ClassNode(**vertex)
                except Exception as e:
                    logger.warning(f"Failed to parse ClassNode: {e}")
                    continue
            else:
                continue

            existing_map[node.id] = {
                "node": node,
                "parent_id": item["parent_id"]
            }

        return existing_map

    def _prepare_new_node(
        self,
        ast_node: BaseNode,
        node_data: Dict[str, Any],
        node_id: str
    ) -> Union[FunctionNode, ClassNode]:
        """
        Create a new node model from AST data.
        """
        position = CodePosition(
            line_no=ast_node.position.line,
            col_offset=ast_node.position.column,
            end_line_no=ast_node.position.end_line,
            end_col_offset=ast_node.position.end_column
        )

        if node_data["type"] == "class":
            mro = node_data.get("mro", [])
            return ClassNode(
                key=node_id,
                name=ast_node.name,
                qname=node_data["qname"],
                position=position,
                implements=mro,
                description=f"Class {ast_node.name}",
                node_type="class"
            )
        else:
            return FunctionNode(
                key=node_id,
                name=ast_node.name,
                qname=node_data["qname"],
                position=position,
                description=f"Function {ast_node.name}",
                node_type="function"
            )

    def _update_existing_node(
        self,
        existing_node: Union[FunctionNode, ClassNode],
        new_node: Union[FunctionNode, ClassNode]
    ) -> None:
        """
        Update existing node fields with new values, preserving other fields
        like created_at, theme_config, documents, etc.
        """
        # Update fields that come from AST parsing
        existing_node.name = new_node.name
        existing_node.qname = new_node.qname
        existing_node.position = new_node.position

        # Update ClassNode-specific fields
        if isinstance(existing_node, ClassNode) and isinstance(new_node, ClassNode):
            existing_node.implements = new_node.implements

    def _determine_sync_operations(
        self,
        desired_nodes_data: List[Dict[str, Any]],
        existing_map: Dict[str, Dict[str, Any]]
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
            full_node_id = f"nodes/{node_id}"
            processed_ids.add(full_node_id)

            existing_entry = existing_map.get(full_node_id)
            existing_node = existing_entry["node"] if existing_entry else None
            existing_parent_id = (
                existing_entry["parent_id"] if existing_entry else None
            )

            # Prepare new node model
            new_node = self._prepare_new_node(ast_node, node_data, node_id)
            current_nodes.append(new_node)

            if not existing_node:
                # Node doesn't exist, create it
                if isinstance(new_node, ClassNode):
                    classes_to_create.append(new_node)
                else:
                    funcs_to_create.append(new_node)

                moves_to_execute.append((node_id, parent_id))
                logger.debug(f"Will create new node: {new_node.qname}")
            else:
                # Node exists, check if update is needed
                needs_update = (
                    existing_node.name != new_node.name or
                    existing_node.qname != new_node.qname or
                    existing_node.position != new_node.position or
                    (isinstance(existing_node, ClassNode) and
                     isinstance(new_node, ClassNode) and
                     existing_node.implements != new_node.implements)
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
                        f"Node moved: {existing_node.qname} -> "
                        f"parent {parent_id}"
                    )
                    moves_to_execute.append((node_id, parent_id))

        # Calculate nodes to delete
        ids_to_delete = [
            sid for sid in existing_map if sid not in processed_ids
        ]

        return {
            "funcs_to_create": funcs_to_create,
            "classes_to_create": classes_to_create,
            "funcs_to_update": funcs_to_update,
            "classes_to_update": classes_to_update,
            "moves_to_execute": moves_to_execute,
            "ids_to_delete": ids_to_delete,
            "current_nodes": current_nodes
        }

    async def _execute_batch_operations(
        self, sync_ops: Dict[str, Any], file_path: str
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

        if funcs_to_create:
            await self.repos.function_repo.create_batch(funcs_to_create)
        if classes_to_create:
            await self.repos.class_repo.create_batch(classes_to_create)

        if funcs_to_update:
            await self.repos.function_repo.update_batch(funcs_to_update)
        if classes_to_update:
            await self.repos.class_repo.update_batch(classes_to_update)

        if moves_to_execute:
            await self.repos.nodes.move_batch(moves_to_execute)

        if ids_to_delete:
            await self.repos.nodes.delete_batch(ids_to_delete)
            logger.info(
                f"Deleted {len(ids_to_delete)} stale nodes {ids_to_delete} in {file_path}"
            )

    def _flatten_nodes(
        self,
        nodes: List[BaseNode],
        parent_node: Union[FileNode, FunctionNode, ClassNode],
        file_path: str,
        content: Optional[str],
        result_list: List[dict]
    ) -> None:
        """Recursively flatten nodes and prepare their metadata."""
        for node in nodes:
            if isinstance(node, (ASTClassNode, ASTFunctionNode)):
                qname = f"{parent_node.qname}.{node.name}"
                node_type = (
                    "class" if isinstance(node, ASTClassNode) else "function"
                )

                mro = []
                if (isinstance(node, ASTClassNode) and
                        self.mro_resolver and content):
                    mro = self._resolve_mro(node, file_path, content)

                node_data = {
                    "qname": qname,
                    "type": node_type,
                    "mro": mro
                }

                result_list.append({
                    "node": node,
                    "node_data": node_data,
                    "parent_id": parent_node.id
                })

                if node.id:
                    node_id = node.id
                else:
                    continue

                if node_type == "class":
                    pseudo_parent = ClassNode(
                        id=node_id,
                        name=node.name,
                        qname=qname,
                        position=CodePosition(
                            line_no=0, col_offset=0,
                            end_line_no=0, end_col_offset=0
                        ),
                        implements=[],
                        description=f"Class {node.name}",
                        node_type="class"
                    )
                else:
                    pseudo_parent = FunctionNode(
                        id=node_id,
                        name=node.name,
                        qname=qname,
                        position=CodePosition(
                            line_no=0, col_offset=0,
                            end_line_no=0, end_col_offset=0
                        ),
                        description=f"Function {node.name}",
                        node_type="function"
                    )

                if hasattr(node, "children"):
                    self._flatten_nodes(
                        node.children, pseudo_parent, file_path,
                        content, result_list
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
                column=name_column + (len(node.name))
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
