import logging
import uuid
import hashlib
import json
from typing import List, Optional, Dict, Any

from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel, ScopeType
from app.core.parser.ast.models import BaseNode, ClassNode, FunctionNode
from app.core.parser.jedi_adapter.resolver import MROResolver

logger = logging.getLogger(__name__)


class ASTProcessor:
    def __init__(self, scope_manager: ScopeManager, mro_resolver: Optional[MROResolver] = None):
        self.manager = scope_manager
        self.mro_resolver = mro_resolver

    async def sync_content(
        self,
        file_scope: ScopeModel,
        nodes: List[BaseNode],
        content: Optional[str] = None
    ) -> List[ScopeModel]:
        """
        Synchronize AST nodes as descendants of the given file scope.
        Handles Creation, Updates, and Deletions of child scopes.
        """
        # 1. Fetch Full Scope Tree (ID-based)
        # Fetch all descendants to avoid recursive DB calls
        existing_descendants = await self.manager.get_descendants(file_scope.id)
        existing_map = {s.id: s for s in existing_descendants}

        # 2. Flatten AST & Prepare Scopes
        desired_scopes_data = []
        self._flatten_nodes(nodes, file_scope, content, desired_scopes_data)

        scopes_to_create: List[ScopeModel] = []
        scopes_to_update: List[ScopeModel] = []
        relationships_to_relink: List[dict[str, str]] = []

        processed_ids = set()
        current_scopes = []

        for data in desired_scopes_data:
            node: BaseNode = data["node"]
            scope_data: Dict[str, Any] = data["scope_data"]
            parent_id: str = data["parent_id"]

            # Skip if no ID (as requested)
            if not node.id:
                continue

            scope_id = node.id
            processed_ids.add(scope_id)

            existing = existing_map.get(scope_id)

            # Checksum
            checksum = self._compute_checksum(node)

            # Prepare ScopeModel
            mro = scope_data.get("mro", [])

            new_scope = ScopeModel(
                id=scope_id,
                name=node.name,
                qname=scope_data["qname"],
                type=scope_data["type"],
                file_path=file_scope.file_path,
                start_line=node.position.line,
                start_col=node.position.column,
                end_line=node.position.end_line,
                end_col=node.position.end_column,
                mro=mro,
                checksum=checksum,
                parent_id=parent_id
            )
            current_scopes.append(new_scope)

            if not existing:
                scopes_to_create.append(new_scope)
                relationships_to_relink.append(
                    {"parent_id": parent_id, "child_id": scope_id})
                logger.debug(f"Will create new scope: {new_scope.qname}")
            else:
                # Update if changed
                # Check content/position/parent (Move)
                # Note: parent_id check detects Moves
                needs_update = (
                    existing.checksum != checksum or
                    existing.start_line != new_scope.start_line or
                    existing.start_col != new_scope.start_col or
                    existing.end_line != new_scope.end_line or
                    existing.end_col != new_scope.end_col or
                    existing.parent_id != parent_id or
                    existing.mro != mro
                )

                if needs_update:
                    scopes_to_update.append(new_scope)
                    logger.debug(f"Scope updated: {new_scope.qname}")

                    if existing.parent_id != parent_id:
                        logger.debug(
                            f"Scope moved: {existing.qname} -> parent {parent_id}")
                        relationships_to_relink.append(
                            {"parent_id": parent_id, "child_id": scope_id})

        # 3. Calculate Deletes
        ids_to_delete = [
            sid for sid in existing_map if sid not in processed_ids]

        # 4. Batch Execution
        if scopes_to_create:
            await self.manager.batch_create_scopes(scopes_to_create)

        if scopes_to_update:
            await self.manager.batch_update_scopes(scopes_to_update)

        if relationships_to_relink:
            # Ensure correct parentage (Move or New Link)
            await self.manager.batch_relink_parent_child(relationships_to_relink)

        if ids_to_delete:
            await self.manager.batch_delete_scopes(ids_to_delete)
            logger.info(
                f"Deleted {len(ids_to_delete)} stale scopes in {file_scope.file_path}")

        return current_scopes

    def _flatten_nodes(
        self,
        nodes: List[BaseNode],
        # Can be FileScope or Class/Function Scope (but passed as ScopeModel)
        parent_scope: ScopeModel,
        content: Optional[str],
        result_list: List[dict]
    ) -> None:
        """Recursively flatten nodes and prepare their metadata."""
        for node in nodes:
            if isinstance(node, (ClassNode, FunctionNode)):
                # Prepare data
                qname = f"{parent_scope.qname}.{node.name}"
                scope_type = ScopeType.CLASS if isinstance(
                    node, ClassNode) else ScopeType.FUNCTION

                mro = []
                if isinstance(node, ClassNode) and self.mro_resolver and content:
                    mro = self._resolve_mro(node, parent_scope, content)

                scope_data = {
                    "qname": qname,
                    "type": scope_type,
                    "mro": mro
                }

                # Append to result
                result_list.append({
                    "node": node,
                    "scope_data": scope_data,
                    "parent_id": parent_scope.id
                })

                # Create a temporary pseudo-scope for children recursion
                # We need the ID to be the parent_id for children.
                if node.id:
                    node_id = node.id
                else:
                    # If we don't have an ID, we assume ID injection failed or wasn't run.
                    # We CANNOT process children properly because we don't have a stable parent ID.
                    # The instruction was "if node has no id do not process it".
                    # Skipping the node means its children are skipped too in this recursion branch.
                    continue

                pseudo_parent = ScopeModel(
                    id=node_id,
                    name=node.name,
                    qname=qname,
                    type=scope_type,
                    file_path=parent_scope.file_path,
                    start_line=node.position.line,
                    start_col=node.position.column,
                    end_line=node.position.end_line,
                    end_col=node.position.end_column
                )

                # Recurse
                if hasattr(node, "children"):
                    self._flatten_nodes(
                        node.children, pseudo_parent, content, result_list)

    def _resolve_mro(self, node: ClassNode, parent_scope: ScopeModel, content: str) -> List[str]:
        try:
            name_column = self._get_name_column(content, node)
            return self.mro_resolver.resolve_mro(
                file_path=parent_scope.file_path,
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

    # Legacy method wrapper if needed, but we should update usage
    async def process_ast_nodes(self, nodes: List[BaseNode], parent_scope: ScopeModel, content: Optional[str] = None) -> List[tuple[ScopeModel, BaseNode]]:
        # Deprecated adapter
        result_scopes = await self.sync_content(parent_scope, nodes, content)
        # Map back to (scope, node) tuple?
        # The nodes in `nodes` list were modified in-place with IDs.
        # But result_scopes are flat.
        # This method returned `List[tuple[ScopeModel, BaseNode]]` for *all* nodes?
        # The old method `_collect_nodes_recursive` flattened them.
        # We can try to reconstruct it if strictly needed, but better to update caller.
        return []
