import logging
from typing import Optional

from app.core.model.nodes import ProjectNode, CallNode
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeType
from app.core.repository import Repositories
from app.core.services.file_service import FileService
from app.core.services.class_service import ClassService
from app.core.services.function_service import FunctionService
from app.core.services.call_service import CallService
from app.core.parser.graph_builder.sync.mappers import (
    map_scope_to_file_node,
    map_scope_to_class_node,
    map_scope_to_function_node,
    map_scope_to_folder_node,
)
from app.core.model.properties import CodePosition
from app.core.model.edges import TargetsEdge

logger = logging.getLogger(__name__)


class MainGraphSyncService:
    """
    Graph Sync Service for synchronizing scope hierarchy to graph database.

    Two-phase approach:
    - Phase 1: Create/update nodes with hierarchy, contains edges, version
    - Version is generated at project level (in orchestrator)
    """

    def __init__(
        self,
        repos: Repositories,
        scope_manager: ScopeManager,
        project_node: ProjectNode,
        sync_version: int,
    ):
        self.repos = repos
        self.scope_manager = scope_manager
        self.project_node = project_node
        self.sync_version = sync_version

        # Initialize services
        self.file_service = FileService(repos)
        self.class_service = ClassService(repos)
        self.function_service = FunctionService(repos)
        self.call_service = CallService(repos)

    def sync_scope_hierarchy(self, root_scope_id: str):
        """
        Phase 1: Sync scope hierarchy starting from root_scope_id.

        Traverses all child scopes and:
        - Creates/updates nodes (only version updated on existing nodes)
        - Establishes contain edges

        Args:
            root_scope_id: The scope ID to start traversal from
        """
        logger.info(
            f"Phase 1: Syncing scope hierarchy from {root_scope_id} "
            f"with version {self.sync_version}"
        )

        root_scope = self.scope_manager.get_scope(root_scope_id)
        if not root_scope:
            logger.error(f"Root scope {root_scope_id} not found")
            return

        # Start from direct children of the root file scope
        child_scopes = self.scope_manager.get_children(root_scope_id)
        for child_scope in child_scopes:
            self._sync_scope_recursive(
                child_scope, parent_node_id=self.project_node.id
            )

    def sync_call_chains(self, root_scope_id: str):
        """
        Phase 2: Sync call chains AFTER scopes are fully synced and
        call sites have been registered in the scope manager.

        This does NOT create CallNode documents – it only:
        - Updates existing call node versions (if found)
        - Ensures/updates targets and contains edges with the version
        """
        logger.info(
            "Phase 2: Syncing call chains from %s with version %s",
            root_scope_id,
            self.sync_version,
        )

        root_scope = self.scope_manager.get_scope(root_scope_id)
        if not root_scope:
            logger.error(
                "Root scope %s not found for call sync", root_scope_id)
            return

        # Simple DFS over scope tree rooted at root_scope
        stack = [root_scope]
        while stack:
            scope = stack.pop()
            if scope.type == ScopeType.FILE or scope.type == ScopeType.FUNCTION or scope.type == ScopeType.CLASS:
                graph_node = self._get_graph_node_for_scope(scope)
                if graph_node:
                    self._sync_root_calls(scope, graph_node.id)

            children = self.scope_manager.get_children(scope.id)
            stack.extend(children)

    def _sync_scope_recursive(self, scope, parent_node_id: str):
        # Map scope to appropriate node type based on scope type
        if scope.type == ScopeType.FILE:
            node = map_scope_to_file_node(scope, self.sync_version)
            saved_node = self._create_or_update_node(
                self.repos.file_repo, node, scope_id=None
            )
        elif scope.type == ScopeType.CLASS:
            node = map_scope_to_class_node(scope, self.sync_version)
            saved_node = self._create_or_update_node(
                self.repos.class_repo, node, scope_id=scope.id
            )
        elif scope.type == ScopeType.FUNCTION:
            node = map_scope_to_function_node(scope, self.sync_version)
            saved_node = self._create_or_update_node(
                self.repos.function_repo, node, scope_id=scope.id
            )
        elif scope.type == ScopeType.FOLDER:
            node = map_scope_to_folder_node(scope, self.sync_version)
            saved_node = self._create_or_update_node(
                self.repos.folder_repo, node, scope_id=scope.id
            )
        else:
            logger.warning(f"Unsupported scope type: {scope.type}")
            return

        # Link to parent with contains edge if parent exists
        if parent_node_id:
            self._ensure_contains_edge(
                parent_node_id, saved_node.id, self.sync_version
            )

        # Recursively process children (scopes only; calls handled in phase 2)
        children = self.scope_manager.get_children(scope.id)
        for child_scope in children:
            self._sync_scope_recursive(
                child_scope,
                parent_node_id=saved_node.id,
            )

    def _get_graph_node_for_scope(self, scope):
        """
        Resolve the graph node corresponding to a given scope.
        """
        if scope.type == ScopeType.FILE:
            return self.repos.file_repo.find_one({"qname": scope.qname})
        if scope.type == ScopeType.CLASS:
            return self.repos.class_repo.get_by_id(scope.id)
        if scope.type == ScopeType.FUNCTION:
            return self.repos.function_repo.get_by_id(scope.id)
        # Folders typically don't own calls directly
        return None

    def _sync_root_calls(self, scope, parent_node_id: str):
        """
        Sync root calls from a scope (calls that originated in this scope).
        Root calls are those starting from file/function/class level.
        """
        try:
            call_infos = self.scope_manager.get_calls_from(scope.id)

            for call_info in call_infos:
                call_site = call_info.get("call_site")
                callee_scope = call_info.get("callee")

                # We only care about resolved calls (have a callee scope)
                if not call_site or not callee_scope:
                    continue

                # Resolve callee node in the main graph
                callee_node = self._get_graph_node_for_scope(callee_scope)
                if not callee_node:
                    continue

                # Find existing CallNode by (parent container, target)
                call_node = self.call_service.get_call_with_parent_and_target(
                    parent_id=parent_node_id,
                    target_id=callee_node.id,
                )

                if not call_node:
                    # No CallNode created for this call in the main graph – skip
                    # create a new CallNode
                    continue

                # Update call node version only (CallNode is the call site)
                try:
                    if call_node.current_version != self.sync_version:
                        call_node.current_version = self.sync_version
                        self.repos.call_repo.update(call_node.key, call_node)
                except Exception as e:
                    logger.error(
                        "Error updating call node %s version: %s",
                        call_node.id,
                        e,
                    )
                    continue

                # Ensure contains edge from parent container -> call
                self._ensure_contains_edge(
                    parent_node_id, call_node.id, self.sync_version
                )

                # Ensure / update targets edge call -> callee
                self._ensure_targets_edge(call_node.id, callee_node.id)

        except Exception as e:
            logger.error(
                f"Error syncing root calls for scope {scope.id}: {e}"
            )

    def _ensure_targets_edge(self, call_id: str, callee_id: str):
        """
        Ensure a targets edge exists between call node and callee.

        Creates if it doesn't exist, updates version if it does.
        """
        try:
            existing_targets = self.repos.targets_edges.find(
                {
                    "from_id": call_id,
                    "to_id": callee_id,
                }
            )

            if existing_targets:
                pass
                # edge = existing_targets[0]
                # if getattr(edge, "version", None) != self.sync_version:
                #     edge.version = self.sync_version
                #     self.repos.targets_edges.update(edge.key, edge)
            else:
                targets_edge = TargetsEdge(
                    from_id=call_id,
                    to_id=callee_id,
                    version=self.sync_version,
                )
                self.repos.targets_edges.create(targets_edge)
        except Exception as e:
            logger.error(
                "Error ensuring targets edge %s -> %s: %s",
                call_id,
                callee_id,
                e,
            )

    def _create_or_update_node(
        self, repo, node, scope_id: Optional[str] = None
    ):
        """
        Create a new node or update existing one.

        Updates version, qname, position if changed.
        Preserves name and description.

        Args:
            repo: The repository to use
            node: The node to create/update
            scope_id: Scope ID (for reference, not used for lookup)

        Returns:
            The created or updated node
        """
        # Lookup existing node by qname
        if scope_id:
            existing = repo.get_by_id(scope_id)
        else:
            existing = repo.find_one({"qname": node.qname})

        if existing:
            # Update version

            existing.current_version = node.current_version

            # Update qname if changed
            if existing.qname != node.qname:
                existing.qname = node.qname

            # Update position if it exists and changed
            if hasattr(existing, 'position') and hasattr(node, 'position'):
                if existing.position != node.position:
                    existing.position = node.position

            return repo.update(existing.key, existing)
        else:
            # Create new
            return repo.create(node)

    def _ensure_contains_edge(
        self, parent_id: str, child_id: str, version: int
    ):
        """
        Ensure a contains edge exists between parent and child.

        Creates if doesn't exist, updates version if it does.
        """
        try:
            # Check if edge already exists
            existing_edges = self.repos.contains_edges.find({
                "from_id": parent_id,
                "to_id": child_id
            })

            if existing_edges:
                # Update edge version
                edge = existing_edges[0]
                if edge.version != version:
                    edge.version = version
                    self.repos.contains_edges.update(edge.key, edge)
            else:
                # Create new edge
                from app.core.model.edges import ContainsEdge

                # Determine contain type from node types
                parent_node = self.repos.nodes.get_by_id(parent_id)
                child_node = self.repos.nodes.get_by_id(child_id)

                if parent_node and child_node:
                    contain_type = (
                        f"{parent_node.node_type}_to_"
                        f"{child_node.node_type}"
                    )
                    edge = ContainsEdge(
                        from_id=parent_id,
                        to_id=child_id,
                        contain_type=contain_type,
                        version=version
                    )
                    self.repos.contains_edges.create(edge)
        except Exception as e:
            logger.error(
                f"Error ensuring contains edge {parent_id} -> "
                f"{child_id}: {e}"
            )
