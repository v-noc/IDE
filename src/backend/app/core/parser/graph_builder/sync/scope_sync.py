import logging

from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel, ScopeType
from app.core.parser.graph_builder.sync.mappers import (
    map_scope_to_file_node,
    map_scope_to_class_node,
    map_scope_to_function_node,
    map_scope_to_folder_node,
)
from app.core.parser.graph_builder.sync.sync_helpers import SyncHelpers

logger = logging.getLogger(__name__)


class ScopeSyncService:
    """Service for syncing scope hierarchy to graph database."""

    def __init__(
        self,
        scope_manager: ScopeManager,
        helpers: SyncHelpers,
    ):
        self.scope_manager = scope_manager
        self.helpers = helpers

    def sync_scope_hierarchy(
        self, root_scope_id: str, project_node_id: str
    ):
        """
        Sync scope hierarchy starting from root_scope_id.

        Traverses all child scopes and:
        - Creates/updates nodes (only version updated on existing nodes)
        - Establishes contain edges

        Args:
            root_scope_id: The scope ID to start traversal from
            project_node_id: The project node ID to use as parent
        """
        logger.info(
            f"Syncing scope hierarchy from {root_scope_id}"
        )

        root_scope = self.scope_manager.get_scope(root_scope_id)
        if not root_scope:
            logger.error(f"Root scope {root_scope_id} not found")
            return

        # Start from direct children of the root file scope
        child_scopes = self.scope_manager.get_children(root_scope_id)
        for child_scope in child_scopes:
            self._sync_scope_recursive(
                child_scope, parent_node_id=project_node_id
            )

    def _sync_scope_recursive(
        self, scope: ScopeModel, parent_node_id: str
    ):
        """
        Recursively sync a scope and its children.

        Args:
            scope: The scope to sync
            parent_node_id: The parent node ID
        """
        # Map scope to appropriate node type based on scope type
        if scope.type == ScopeType.FILE:
            node = map_scope_to_file_node(scope, self.helpers.sync_version)
            saved_node = self.helpers.create_or_update_node(
                self.helpers.repos.file_repo, node, scope_id=None
            )
        elif scope.type == ScopeType.CLASS:
            node = map_scope_to_class_node(scope, self.helpers.sync_version)
            saved_node = self.helpers.create_or_update_node(
                self.helpers.repos.class_repo, node, scope_id=scope.id
            )
        elif scope.type == ScopeType.FUNCTION:
            node = map_scope_to_function_node(
                scope, self.helpers.sync_version
            )
            saved_node = self.helpers.create_or_update_node(
                self.helpers.repos.function_repo, node, scope_id=scope.id
            )
        elif scope.type == ScopeType.FOLDER:
            node = map_scope_to_folder_node(
                scope, self.helpers.sync_version
            )
            saved_node = self.helpers.create_or_update_node(
                self.helpers.repos.folder_repo, node, scope_id=scope.id
            )
        else:
            logger.warning(f"Unsupported scope type: {scope.type}")
            return

        # Link to parent with contains edge if parent exists
        if parent_node_id:
            self.helpers.ensure_contains_edge(
                parent_node_id,
                saved_node.id,
                self.helpers.sync_version
            )

        # Recursively process children (scopes only; calls handled separately)
        children = self.scope_manager.get_children(scope.id)
        for child_scope in children:
            self._sync_scope_recursive(
                child_scope,
                parent_node_id=saved_node.id,
            )
