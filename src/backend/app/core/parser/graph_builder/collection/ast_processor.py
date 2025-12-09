from app.core.parser.jedi_adapter.resolver import MROResolver
import logging
import uuid
import hashlib
import json
from typing import List, Tuple, Any, Optional, Dict

from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel, ScopeType
from app.core.parser.ast.models import BaseNode, ClassNode, FunctionNode

logger = logging.getLogger(__name__)


class ASTProcessor:
    def __init__(self, scope_manager: ScopeManager, mro_resolver: Optional[MROResolver] = None):
        self.manager = scope_manager
        self.mro_resolver = mro_resolver

    def process_ast_nodes(self, nodes: List[BaseNode], parent_scope: ScopeModel, content: Optional[str] = None) -> List[tuple[ScopeModel, BaseNode]]:
        """
        Recursively create scopes for AST nodes and return created scopes with their AST nodes.
        Uses batch operations for efficiency.
        """
        # First pass: collect all nodes and their metadata
        node_data_list = []
        self._collect_nodes_recursive(
            nodes, parent_scope, content, node_data_list)

        if not node_data_list:
            return []

        # Extract all scope IDs that need to be checked
        scope_ids_to_check = [data["node_id"] for data in node_data_list]

        # Batch check all existing scopes
        existing_scopes = self.manager.batch_get_scopes_by_ids(
            scope_ids_to_check)

        # Collect scopes to create, update, and relationships to link
        scopes_to_create: List[ScopeModel] = []
        scopes_to_update: List[ScopeModel] = []
        relationships_to_link: List[dict[str, str]] = []
        scope_map: Dict[str, ScopeModel] = {}  # node_id -> scope

        # Process each node data
        for data in node_data_list:
            node = data["node"]
            node_id = data["node_id"]
            scope = data["scope"]
            parent_scope_obj = data["parent_scope"]

            existing = existing_scopes.get(node_id)

            if not existing:
                # New scope - mark for creation
                scopes_to_create.append(scope)
                relationships_to_link.append({
                    "parent_id": parent_scope_obj.id,
                    "child_id": node_id
                })
                logger.debug(f"Will create new scope: {scope.qname}")
            else:
                # Existing scope - check if it needs updating
                needs_update = False
                needs_relink = False

                # Check if checksum changed (content change)
                if existing.checksum != scope.checksum:
                    needs_update = True
                    logger.debug(f"Scope content changed: {scope.qname}")

                # Check if position changed
                if (existing.start_line != scope.start_line or
                    existing.start_col != scope.start_col or
                    existing.end_line != scope.end_line or
                        existing.end_col != scope.end_col):
                    needs_update = True
                    logger.debug(f"Scope position changed: {scope.qname}")

                # Check if qname changed (moved to different parent or renamed)
                if existing.qname != scope.qname:
                    needs_update = True
                    needs_relink = True
                    logger.debug(
                        f"Scope moved or renamed: {existing.qname} -> {scope.qname}")

                # Check if MRO changed (if we have new MRO)
                if scope.mro and existing.mro != scope.mro:
                    needs_update = True
                    logger.debug(f"Scope MRO changed: {scope.qname}")

                if needs_update:
                    scopes_to_update.append(scope)

                if needs_relink:
                    # TODO: Handle parent change - need to remove old parent link
                    relationships_to_link.append({
                        "parent_id": parent_scope_obj.id,
                        "child_id": node_id
                    })
                    pass

                # Use existing scope for the result
                scope = existing

            scope_map[node_id] = scope

        # Batch create all scopes
        if scopes_to_create:
            self.manager.batch_create_scopes(scopes_to_create)

        # Batch update all scopes
        if scopes_to_update:
            self.manager.batch_update_scopes(scopes_to_update)

        # Batch link all parent-child relationships
        if relationships_to_link:
            self.manager.batch_link_parent_child(relationships_to_link)

        # Build results list
        results = []
        for data in node_data_list:
            node_id = data["node_id"]
            node = data["node"]
            scope = scope_map[node_id]
            results.append((scope, node))

        return results

    def _collect_nodes_recursive(
        self,
        nodes: List[BaseNode],
        parent_scope: ScopeModel,
        content: Optional[str],
        node_data_list: List[dict]
    ) -> None:
        """Recursively collect all nodes and build their scope models."""
        for node in nodes:
            if isinstance(node, (ClassNode, FunctionNode)):
                node_data = self._prepare_node_scope(
                    node, parent_scope, content)
                node_data_list.append(node_data)

                # Get the scope for recursion
                scope = node_data["scope"]

                # Recurse into children
                if hasattr(node, "children"):
                    self._collect_nodes_recursive(
                        node.children, scope, content, node_data_list
                    )

    def _prepare_node_scope(self, node: BaseNode, parent_scope: ScopeModel, content: Optional[str] = None) -> dict:
        """
        Prepare scope data for an AST node without creating it yet.
        Returns a dict with node, node_id, scope, and parent_scope.
        """
        # Determine ID: Use injected ID if available, else generate
        node_id = node.id if node.id else str(uuid.uuid4())
        node.id = node_id  # Persist ID on node for Phase 2

        # Construct QName
        qname = f"{parent_scope.qname}.{node.name}"

        scope_type = ScopeType.CLASS if isinstance(
            node, ClassNode) else ScopeType.FUNCTION

        mro = []
        name_column = node.position.column
        if isinstance(node, ClassNode) and self.mro_resolver and content:
            # Resolve MRO using Jedi
            # Note: Jedi uses 1-based lines. Our AST scanner uses 1-based lines.
            try:
                name_column = self._get_name_column(content, node)
                mro = self.mro_resolver.resolve_mro(
                    file_path=parent_scope.file_path,
                    source=content,
                    line=node.position.line,
                    column=node.position.column + (len(node.name))
                )
                if mro:
                    logger.debug(f"Resolved MRO for {node.name}: {mro}")
                    # Base classes are typically the immediate parents in MRO (excluding self and object)
                    # But extracting exact base classes from MRO is tricky without AST analysis of bases.
                    # For now, we can leave base_classes empty or try to parse them from AST if available.
                    # The user asked for MRO specifically.
            except Exception as e:
                logger.error(f"Failed to resolve MRO for {node.name}: {e}")

        # Compute Checksum
        checksum = self._compute_checksum(node)

        # Build the scope model
        scope = ScopeModel(
            id=node_id,
            name=node.name,
            qname=qname,
            type=scope_type,
            file_path=parent_scope.file_path,
            start_line=node.position.line,
            start_col=node.position.column,
            end_line=node.position.end_line,
            end_col=node.position.end_column,
            mro=mro,
            checksum=checksum,
            parent_id=parent_scope.id
        )

        return {
            "node": node,
            "node_id": node_id,
            "scope": scope,
            "parent_scope": parent_scope
        }

    def _get_name_column(self, content: str, node: BaseNode) -> int:
        """
        Approximate the column where the identifier name starts on its line.
        Required for Jedi inference which expects the cursor on the identifier.
        """
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
        """
        Compute a deterministic checksum for the AST node.
        We use the node's name, type, and position (and children recursively?)
        Actually, if content changes, position might change.
        If we want to detect *content* change, we should ideally hash the source code.
        But we don't have source code here easily (unless passed).
        For now, let's hash the node attributes.
        If we want to be strict, any change in children should bubble up?
        The user said "if function or class change add append them and thier children".
        This implies a change in a child might not affect the parent's *own* body (calls),
        but we should process the child.
        Let's hash the node's relevant fields.
        """
        # Simple hash of the node's dictionary representation
        # We need to be careful about unstable fields (like ID if we just generated it, but we set it).
        # We exclude ID from hash to check for content equality?
        # No, we want to check if *this* version is different from DB.
        # DB has checksum of previous version.
        data = node.model_dump(exclude={"id", "children"})
        # We should also include children's checksums?
        # If a child changes, does the parent change?
        # Usually yes, but for "Scope" tracking, maybe not.
        # But for "Body" analysis (Calls), if I change a call inside a function, the function checksum should change.
        # Calls are children in the AST.
        # So yes, we should include children in the hash.
        # But `model_dump` with children might be recursive.
        data["children_hash"] = self._hash_children(node.children)

        encoded = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _hash_children(self, children: List[BaseNode]) -> str:
        if not children:
            return ""
        hashes = []
        for child in children:
            # We can't fully recurse if deep, but AST isn't too deep.
            # We just need a representation.
            hashes.append(child.name + child.type + str(child.position))
        return hashlib.sha256("".join(hashes).encode("utf-8")).hexdigest()
