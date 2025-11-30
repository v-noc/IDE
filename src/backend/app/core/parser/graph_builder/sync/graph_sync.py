import logging
from typing import Optional

from app.core.model.nodes import ProjectNode
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeType
from app.core.repository import Repositories
from app.core.services.file_service import FileService
from app.core.services.class_service import ClassService
from app.core.services.function_service import FunctionService
from app.core.parser.graph_builder.sync.mappers import (
    map_scope_to_file_node,
    map_scope_to_class_node,
    map_scope_to_function_node,
    map_scope_to_folder_node,
)

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
        child_scopes = self.scope_manager.get_children(root_scope_id)

        for child_scope in child_scopes:
            self._sync_scope_recursive(
                child_scope, parent_node_id=self.project_node.id)

        for child_scope in child_scopes:
            self._sync_scope_recursive(
                child_scope, parent_node_id=self.project_node.id)

    def _sync_child_calls(self, scope, parent_node_id: str):
        child_calls = self.scope_manager.get_calls_from(scope.id)

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

        # Recursively process children
        children = self.scope_manager.get_children(scope.id)
        for child_scope in children:
            self._sync_scope_recursive(
                child_scope, parent_node_id=saved_node.id, scope_id=scope.id
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
