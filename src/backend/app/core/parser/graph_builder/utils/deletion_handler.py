"""Handles deletion of files and folders in the graph."""
import logging
from pathlib import Path
from typing import Optional

from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.collection.hierarchy import FolderChange
from app.core.parser.graph_builder.utils import PathResolver
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel

logger = logging.getLogger(__name__)


class DeletionHandler:
    """Handles deletion of files and folders."""

    def __init__(
        self,
        project_node: ProjectNode,
        scope_manager: ScopeManager,
        path_resolver: PathResolver,
    ):
        self.project_node = project_node
        self.project_root = Path(project_node.path)
        self.scope_manager = scope_manager
        self.path_resolver = path_resolver

    async def handle_folder_deletion(
        self,
        folder_path: str,
        folder_changes: list,
        touched_folder_ids: set,
    ) -> None:
        """
        Handle deletion of a folder.

        Args:
            folder_path: Absolute path to the folder
            folder_changes: List to append folder changes to
            touched_folder_ids: Set of folder IDs that have been touched
        """
        folder_scope = self.path_resolver.scope_from_path(
            folder_path, is_file=False
        )
        if not folder_scope:
            logger.warning(
                "Folder scope not found for deletion path: %s", folder_path
            )
            return

        self._append_folder_change(
            folder_changes, touched_folder_ids, folder_scope, "deleted"
        )
        await self.scope_manager.delete_scope(folder_scope.id)

    async def handle_file_deletion(
        self,
        file_path: str,
        folder_changes: list,
        touched_folder_ids: set,
    ) -> None:
        """
        Handle deletion of a file.

        Args:
            file_path: Absolute path to the file
            folder_changes: List to append folder changes to
            touched_folder_ids: Set of folder IDs that have been touched
        """
        await self.scope_manager.delete_file_scope(file_path)
        await self._touch_parent_folders(
            file_path, folder_changes, touched_folder_ids)

    async def _touch_parent_folders(
        self,
        target_path: str,
        folder_changes: list,
        touched_folder_ids: set,
    ) -> None:
        """
        Mark parent folders as updated when a child is deleted.

        Args:
            target_path: Path to the deleted file/folder
            folder_changes: List to append folder changes to
            touched_folder_ids: Set of folder IDs that have been touched
        """
        try:
            rel_path = Path(target_path).relative_to(self.project_root)
        except ValueError:
            logger.warning(
                "Path %s is outside project root %s",
                target_path,
                self.project_root,
            )
            return

        folder_parts = rel_path.parts[:-1]
        if not folder_parts:
            return

        current_qname = self.project_node.name

        for part in folder_parts:
            current_qname = f"{current_qname}.{part}"
            folder_scope = await self.scope_manager.get_scope_by_qname(current_qname)
            if not folder_scope or folder_scope.id in touched_folder_ids:
                continue
            self._append_folder_change(
                folder_changes, touched_folder_ids, folder_scope, "updated"
            )

    async def handle_batch_folder_deletions(
        self,
        folder_paths: list[str],
        folder_changes: list,
        touched_folder_ids: set,
    ) -> None:
        """
        Handle batch deletion of multiple folders.

        Args:
            folder_paths: List of absolute paths to folders
            folder_changes: List to append folder changes to
            touched_folder_ids: Set of folder IDs that have been touched
        """
        if not folder_paths:
            return

        logger.info(
            f"Processing batch deletion of {len(folder_paths)} folders")

        # Resolve all folder scopes first
        folder_scopes_to_delete = []
        for folder_path in folder_paths:
            folder_scope = self.path_resolver.scope_from_path(
                folder_path, is_file=False
            )
            if folder_scope:
                folder_scopes_to_delete.append(folder_scope)
            else:
                logger.warning(
                    "Folder scope not found for deletion path: %s", folder_path
                )

        # Batch process folder changes
        for folder_scope in folder_scopes_to_delete:
            self._append_folder_change(
                folder_changes, touched_folder_ids, folder_scope, "deleted"
            )

        # Batch delete all scopes and their children/relationships
        if folder_scopes_to_delete:
            scope_ids_to_delete = [
                scope.id for scope in folder_scopes_to_delete]
            await self.scope_manager.batch_delete_scopes(scope_ids_to_delete)

    async def handle_batch_file_deletions(
        self,
        file_paths: list[str],
        folder_changes: list,
        touched_folder_ids: set,
    ) -> None:
        """
        Handle batch deletion of multiple files.

        Args:
            file_paths: List of absolute paths to files
            folder_changes: List to append folder changes to
            touched_folder_ids: Set of folder IDs that have been touched
        """
        if not file_paths:
            return

        logger.info(f"Processing batch deletion of {len(file_paths)} files")

        # Batch delete all file scopes and their children/relationships
        await self.scope_manager.batch_delete_file_scopes(file_paths)

        # Batch touch parent folders
        for file_path in file_paths:
            await self._touch_parent_folders(
                file_path, folder_changes, touched_folder_ids)

    def _append_folder_change(
        self,
        folder_changes: list,
        touched_folder_ids: set,
        scope: Optional[ScopeModel],
        action: str,
    ) -> None:
        """
        Append a folder change if the scope hasn't been touched yet.

        Args:
            folder_changes: List to append to
            touched_folder_ids: Set to track touched folders
            scope: Scope to add change for
            action: Action type ("created", "updated", "deleted")
        """
        if not scope or scope.id in touched_folder_ids:
            return
        folder_changes.append(FolderChange(scope=scope, action=action))
        touched_folder_ids.add(scope.id)
