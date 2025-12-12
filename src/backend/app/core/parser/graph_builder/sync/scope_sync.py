import logging
from typing import Optional

from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel, ScopeType
from app.core.parser.graph_builder.sync.mappers import (
    map_scope_to_file_node,
    map_scope_to_class_node,
    map_scope_to_function_node,
    map_scope_to_folder_node,
)
from app.core.parser.graph_builder.sync.sync_helpers import SyncHelpers
from app.core.parser.graph_builder.discovery.change_detector import ChangeSet

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
        self, root_scope_id: str, project_node_id: str, change_set: Optional[ChangeSet] = None
    ):
        """
        Sync scope hierarchy starting from root_scope_id.

        Traverses all child scopes and:
        - Creates/updates nodes (only version updated on existing nodes)
        - Establishes contain edges

        If change_set is provided, only syncs scopes that are in the change set.
        Items not in change set are skipped (no recursion).

        Args:
            root_scope_id: The scope ID to start traversal from
            project_node_id: The project node ID to use as parent
            change_set: Optional ChangeSet to filter what gets synced
        """
        if change_set:
            logger.info(
                f"Incremental sync from {root_scope_id}: "
                f"{len(change_set.new_files)} new, "
                f"{len(change_set.modified_files)} modified, "
                f"{len(change_set.deleted_files)} deleted files, "
                f"{len(change_set.new_folders)} new, "
                f"{len(change_set.deleted_folders)} deleted folders"
            )
        else:
            logger.info(f"Full sync from {root_scope_id}")

        root_scope = self.scope_manager.get_scope(root_scope_id)
        if not root_scope:
            logger.error(f"Root scope {root_scope_id} not found")
            return

        # Start from direct children of the root file scope
        child_scopes = self.scope_manager.get_children(root_scope_id)
        for child_scope in child_scopes:
            self._sync_scope_recursive(
                child_scope, parent_node_id=project_node_id, change_set=change_set
            )

    def _sync_scope_recursive(
        self, scope: ScopeModel, parent_node_id: str, change_set: Optional[ChangeSet] = None
    ):
        """
        Recursively sync a scope and its children.

        If change_set is provided:
        - For files: check if in new_files, modified_files, or deleted_files
        - For folders: check if in new_folders or deleted_folders
        - If not in change set: skip entirely (no recursion)
        - If deleted: sync with negative version and skip recursion

        Args:
            scope: The scope to sync
            parent_node_id: The parent node ID
            change_set: Optional ChangeSet to filter what gets synced
        """
        # Check if this scope should be synced
        # Only files and folders check change set
        # Classes and functions always sync (they're children of files)
        if change_set:
            is_in_change_set = False
            is_deleted = False
            version = self.helpers.sync_version

            if scope.type == ScopeType.FILE:
                is_in_change_set = (
                    scope.file_path in change_set.new_files or
                    scope.file_path in change_set.modified_files or
                    scope.file_path in change_set.deleted_files
                )
                is_deleted = scope.file_path in change_set.deleted_files
            elif scope.type == ScopeType.FOLDER:
                is_in_change_set = (
                    scope.file_path in change_set.new_folders or
                    scope.file_path in change_set.deleted_folders
                )
                is_deleted = scope.file_path in change_set.deleted_folders
            elif scope.type in (ScopeType.CLASS, ScopeType.FUNCTION):
                # Classes and functions always sync (they're children of files)
                # If parent file is being synced, sync them too
                is_in_change_set = True
                is_deleted = False
            else:
                # Unknown type, skip
                return

            # For files and folders: if not in change set, skip entirely
            if scope.type in (ScopeType.FILE, ScopeType.FOLDER) and not is_in_change_set:
                return

            # If deleted, use negative version
            if is_deleted:
                version = -self.helpers.sync_version
        else:
            version = self.helpers.sync_version
            is_deleted = False

        # Map scope to appropriate node type based on scope type
        if scope.type == ScopeType.FILE:
            node = map_scope_to_file_node(scope, version)
            saved_node = self.helpers.create_or_update_node(
                self.helpers.repos.file_repo, node, scope_id=None
            )
        elif scope.type == ScopeType.CLASS:
            node = map_scope_to_class_node(scope, version)
            saved_node = self.helpers.create_or_update_node(
                self.helpers.repos.class_repo, node, scope_id=scope.id
            )
        elif scope.type == ScopeType.FUNCTION:
            node = map_scope_to_function_node(scope, version)
            saved_node = self.helpers.create_or_update_node(
                self.helpers.repos.function_repo, node, scope_id=scope.id
            )
        elif scope.type == ScopeType.FOLDER:
            node = map_scope_to_folder_node(scope, version)
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
                version
            )

        # If deleted, don't recurse into children
        if is_deleted:
            return

        # Recursively process children (scopes only; calls handled separately)
        children = self.scope_manager.get_children(scope.id)
        for child_scope in children:
            self._sync_scope_recursive(
                child_scope,
                parent_node_id=saved_node.id,
                change_set=change_set
            )
