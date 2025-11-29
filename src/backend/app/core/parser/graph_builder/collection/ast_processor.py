from app.core.parser.jedi_adapter.resolver import MROResolver
import logging
import uuid
import hashlib
import json
from typing import List, Tuple, Any, Optional

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
        """
        results = []
        for node in nodes:
            if isinstance(node, (ClassNode, FunctionNode)):
                scope = self._create_node_scope(node, parent_scope, content)
                results.append((scope, node))

                # Recurse
                if hasattr(node, "children"):
                    child_results = self.process_ast_nodes(
                        node.children, scope, content)
                    results.extend(child_results)
        return results

    def _create_node_scope(self, node: BaseNode, parent_scope: ScopeModel, content: Optional[str] = None):
        """
        Create or update a scope for an AST node.
        Handles new scopes, modified scopes, and scope moves.
        """
        # Determine ID: Use injected ID if available, else generate
        node_id = node.id if node.id else str(uuid.uuid4())
        node.id = node_id  # Persist ID on node for Phase 2

        # Construct QName
        qname = f"{parent_scope.qname}.{node.name}"

        scope_type = ScopeType.CLASS if isinstance(
            node, ClassNode) else ScopeType.FUNCTION

        mro = []
        if isinstance(node, ClassNode) and self.mro_resolver and content:
            # Resolve MRO using Jedi
            # Note: Jedi uses 1-based lines. Our AST scanner uses 1-based lines.
            try:
                mro = self.mro_resolver.resolve_mro(
                    file_path=parent_scope.file_path,
                    source=content,
                    line=node.position.line,
                    column=node.position.column
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
            checksum=checksum
        )

        # Check if scope exists
        existing = self.manager.get_scope(node_id)

        if not existing:
            # New scope - create it
            self.manager.create_scope(
                name=node.name,
                qname=qname,
                scope_type=scope_type,
                file_path=parent_scope.file_path,
                start_line=node.position.line,
                start_col=node.position.column,
                end_line=node.position.end_line,
                end_col=node.position.end_column,
                scope_id=node_id,
                mro=mro,
                checksum=checksum
            )
            # Link to parent
            self.manager.link_parent_child(parent_scope.id, node_id)
            logger.debug(f"Created new scope: {qname}")
        else:
            # Existing scope - check if it needs updating
            needs_update = False
            needs_relink = False

            # Check if checksum changed (content change)
            if existing.checksum != checksum:
                needs_update = True
                logger.debug(f"Scope content changed: {qname}")

            # Check if position changed
            if (existing.start_line != node.position.line or
                existing.start_col != node.position.column or
                existing.end_line != node.position.end_line or
                    existing.end_col != node.position.end_column):
                needs_update = True
                logger.debug(f"Scope position changed: {qname}")

            # Check if qname changed (moved to different parent or renamed)
            if existing.qname != qname:
                needs_update = True
                needs_relink = True
                logger.debug(
                    f"Scope moved or renamed: {existing.qname} -> {qname}")

            # Check if MRO changed (if we have new MRO)
            if mro and existing.mro != mro:
                needs_update = True
                logger.debug(f"Scope MRO changed: {qname}")

            if needs_update:
                # Update the scope in database
                self.manager.update_scope(scope)

            if needs_relink:
                # TODO: Handle parent change - need to remove old parent link
                pass

        return scope

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
