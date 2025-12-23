import logging
from pathlib import Path
from typing import Optional, Set

from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel, ScopeType
from app.core.parser.graph_builder.sync.mappers import (
    map_scope_to_file_node,
    map_scope_to_class_node,
    map_scope_to_function_node,
    map_scope_to_folder_node,
)
from app.core.parser.graph_builder.sync.async_helpers import AsyncSyncHelpers
from app.core.parser.graph_builder.discovery.change_detector import ChangeSet
import asyncio

from app.core.model.base import BaseNode
logger = logging.getLogger(__name__)


class ScopeSyncService:
    """Service for syncing scope hierarchy to graph database."""

    def __init__(
        self,
        scope_manager: ScopeManager,
        helpers: AsyncSyncHelpers,
    ):
        self.scope_manager = scope_manager
        self.helpers = helpers

    async def sync_scope_hierarchy(
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

        touched_folders = self._build_touched_folders(change_set)
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

        # Get direct children of root
        children = self.scope_manager.get_children(root_scope_id)

        # Process all children concurrently
        await asyncio.gather(*[
            self._sync_scope_async(
                child,
                parent_node_id=project_node_id,
                change_set=change_set,
                touched_folders=touched_folders
            )
            for child in children
        ])

    def _build_touched_folders(self, change_set: ChangeSet) -> Set[str]:
        """Build set of folders that need sync due to file changes."""
        touched = set()

        # Explicit folder changes
        touched.update(change_set.new_folders)
        touched.update(change_set.deleted_folders)

        # Folders containing file changes
        all_changed_files = (
            change_set.new_files +
            change_set.modified_files +
            change_set.deleted_files
        )

        for file_path in all_changed_files:
            parent = Path(file_path).parent
            while parent != parent.parent:
                touched.add(str(parent))
                parent = parent.parent

        return touched

    async def _sync_scope_async(
        self,
        scope: ScopeModel,
        parent_node_id: str,
        change_set: ChangeSet,
        touched_folders: Set[str],
    ) -> None:

        should_sync = False
        should_recurse = False
        is_deleted = False

        if scope.type == ScopeType.FILE:
            if scope.file_path in change_set.new_files:
                should_sync = True
                should_recurse = True
            elif scope.file_path in change_set.modified_files:
                should_sync = True
                should_recurse = True
            elif scope.file_path in change_set.deleted_files:
                should_sync = True
                is_deleted = True
                should_recurse = False

        elif scope.type == ScopeType.FOLDER:
            # Sync if explicitly changed OR contains changed files
            if scope.file_path in touched_folders:
                should_sync = True
            # ALWAYS recurse into folders to find changed files
            should_recurse = True

        elif scope.type in (ScopeType.CLASS, ScopeType.FUNCTION):
            # Always sync if we're visiting (parent was synced)
            should_sync = True
            should_recurse = True

        # Perform sync if needed
        if should_sync:
            saved_node = await self._sync_single_scope(
                scope, parent_node_id, is_deleted
            )
            # Update parent_node_id for children
            if saved_node:
                parent_node_id = saved_node.id

        # Recurse into children (concurrently)
        if should_recurse and not is_deleted:
            children = self.scope_manager.get_children(scope.id)
            if children:
                await asyncio.gather(*[
                    self._sync_scope_async(
                        child,
                        parent_node_id=parent_node_id,
                        change_set=change_set,
                        touched_folders=touched_folders,
                    )
                    for child in children
                ])

    async def _sync_single_scope(
        self,
        scope: ScopeModel,
        parent_node_id: str,
        is_deleted: bool = False,
    ) -> Optional[BaseNode]:
        """Sync a single scope to the graph database."""
        from .mappers import (
            map_scope_to_file_node,
            map_scope_to_folder_node,
            map_scope_to_class_node,
            map_scope_to_function_node,
        )

        # Map to appropriate node type
        if scope.type == ScopeType.FILE:
            node = map_scope_to_file_node(scope)
        elif scope.type == ScopeType.FOLDER:
            node = map_scope_to_folder_node(scope)
        elif scope.type == ScopeType.CLASS:
            node = map_scope_to_class_node(scope)
        elif scope.type == ScopeType.FUNCTION:
            node = map_scope_to_function_node(scope)
        else:
            return None

        # Handle deletion (soft delete or remove)
        if is_deleted:
            await self.helpers.mark_node_deleted(node.id)
            return None

        # Create or update node
        saved_node = await self.helpers.async_create_or_update_node(
            node, scope_id=scope.id
        )

        # Ensure contains edge
        if parent_node_id and saved_node:
            await self.helpers.async_ensure_contains_edge(
                parent_node_id, saved_node.id
            )

        return saved_node
