import asyncio
import datetime
import logging
from pathlib import Path
from typing import Optional, Set

from app.core.model.base import BaseNode
from app.core.parser.graph_builder.discovery.change_detector import ChangeSet
from app.core.parser.graph_builder.sync.async_helpers import AsyncSyncHelpers
from app.core.parser.graph_builder.sync.mappers import (
    map_scope_to_class_node,
    map_scope_to_file_node,
    map_scope_to_folder_node,
    map_scope_to_function_node,
)
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel, ScopeType

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
        self,
        root_scope_id: str,
        project_node_id: str,
        change_set: Optional[ChangeSet] = None,
    ):
        """Main entry point for hierarchy synchronization."""
        touched_folders = (
            self._build_touched_folders(change_set) if change_set else set()
        )

        # In this unified strategy, the root children are synced first
        children = await self.scope_manager.get_children(root_scope_id)

        # Track current child IDs to orphan missing ones at the project root level
        current_child_ids = {f"nodes/{child.id}" for child in children}

        await asyncio.gather(
            *[
                self._sync_scope_async(
                    child,
                    parent_node_id=project_node_id,
                    change_set=change_set,
                    touched_folders=touched_folders,
                )
                for child in children
            ]
        )

        # Cleanup: Mark nodes that exist in DB under project but aren't in AST anymore
        await self._mark_missing_children_orphaned(project_node_id, current_child_ids)

    def _build_touched_folders(self, change_set: ChangeSet) -> Set[str]:
        """Build set of folders that need sync due to file changes."""
        touched = set()

        # Explicit folder changes
        touched.update(change_set.new_folders)
        touched.update(change_set.deleted_folders)

        # Folders containing file changes
        all_changed_files = (
            change_set.new_files + change_set.modified_files + change_set.deleted_files
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
        change_set: Optional[ChangeSet],
        touched_folders: Set[str],
    ) -> None:
        """Recursive unified sync logic."""

        # 1. Determine if we need to sync this specific node
        should_sync, should_recurse = self._determine_sync_necessity(
            scope, change_set, touched_folders
        )

        if should_sync:
            # 2. Unified Sync Logic (Create / Update / Move)
            # This replaces the old _sync_single_scope
            saved_node = await self._unified_sync_node(scope, parent_node_id)
            if saved_node:
                parent_node_id = saved_node.id

        # 3. Recurse into children
        if should_recurse:
            children = await self.scope_manager.get_children(scope.id)
            current_child_ids = set()
            if children:
                current_child_ids.update({f"nodes/{c.id}" for c in children})

                # Sync children concurrently
                await asyncio.gather(
                    *[
                        self._sync_scope_async(
                            child, parent_node_id, change_set, touched_folders
                        )
                        for child in children
                    ]
                )

            # 4. Cleanup: Soft-delete children no longer present in AST under this parent
            await self._mark_missing_children_orphaned(
                parent_node_id, current_child_ids
            )

    def _map_scope_to_node(self, scope: ScopeModel) -> BaseNode:
        """Map ScopeModel to BaseNode."""
        if scope.type == ScopeType.FOLDER:
            return map_scope_to_folder_node(scope)
        elif scope.type == ScopeType.FILE:
            return map_scope_to_file_node(scope)
        elif scope.type == ScopeType.CLASS:
            return map_scope_to_class_node(scope)
        elif scope.type == ScopeType.FUNCTION:
            return map_scope_to_function_node(scope)
        else:
            raise ValueError(f"Unsupported scope type: {scope.type}")

    async def _unified_sync_node(
        self, scope: ScopeModel, expected_parent_id: str
    ) -> Optional[BaseNode]:
        """Implementation of the 08 Decision Table: Create, Update, or Re-parent."""
        node_id = f"nodes/{scope.id}"
        existing_node = await self.helpers.async_get_node_by_id(node_id)

        if not existing_node:
            # ACTION: CREATE
            node = self._map_scope_to_node(scope)
            saved_node = await self.helpers.async_create_node(node)
            await self.helpers.async_ensure_contains_edge(expected_parent_id, node_id)
            return saved_node

        # Check current parent to detect moves
        current_parent_id = await self.helpers.async_get_parent_id(node_id)

        if current_parent_id == expected_parent_id:
            # ACTION: UPDATE (Same parent, just refresh properties)
            existing_node.status = "active"
            # existing_node.status_changed_at = datetime.now()
            existing_node.orphan_reason = None
            saved_node = await self.helpers.async_update_node_properties(
                existing_node, scope
            )
            return saved_node
        else:
            # ACTION: RE-PARENT (Move)
            await self.helpers.async_move_node(
                node_id, current_parent_id, expected_parent_id
            )
            existing_node.status = "active"
            # existing_node.status_changed_at = datetime.now()
            existing_node.orphan_reason = None
            saved_node = await self.helpers.async_update_node_properties(
                existing_node, scope
            )
            return saved_node

    def _determine_sync_necessity(
        self,
        scope: ScopeModel,
        change_set: Optional[ChangeSet],
        touched_folders: Set[str],
    ):
        """Logic to decide if we should process or skip this scope."""
        if not change_set:  # Full sync
            return True, True

        if scope.type == ScopeType.FOLDER:
            return (scope.file_path in touched_folders), True
        if scope.type == ScopeType.FILE:
            is_changed = (
                scope.file_path in change_set.new_files
                or scope.file_path in change_set.modified_files
            )
            return is_changed, is_changed

        # Classes/Functions: If parent (file) is being synced, they are visited
        return True, True

    async def _mark_missing_children_orphaned(
        self, parent_id: str, current_child_ids: Set[str]
    ):
        """Soft-delete nodes that exist in DB but not in current AST parse."""
        db_children = await self.helpers.async_get_children(
            parent_id,
            [ScopeType.FOLDER, ScopeType.FILE, ScopeType.CLASS, ScopeType.FUNCTION],
        )

        for child in db_children:
            if child.get("_id") not in current_child_ids:
                await self.helpers.async_mark_node_status(
                    child, status="orphaned", reason="not_in_ast_under_same_parent"
                )
