import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import aiofiles
import asyncio
from app.core.model.nodes import ProjectNode
from app.core.parser.ast.scanner import scan
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.parser.jedi_adapter.resolver import MROResolver
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel
from app.core.parser.graph_builder.discovery.change_detector import ChangeSet
from app.core.parser.graph_builder.discovery.scanner import ScanResult

from .ast_processor import ASTProcessor
from .folder_processor import FolderProcessor, FolderChange
from .file_processor import FileProcessor

logger = logging.getLogger(__name__)


@dataclass
class CollectionResult:
    file_scope: ScopeModel
    removed_scope_ids: List[str]  # IDs of scopes that were deleted
    folder_changes: List[FolderChange]


class Collector:
    def __init__(
        self,
        project_node: ProjectNode,
        scope_manager: ScopeManager,
        jedi_manager: JediProjectManager,
    ):
        self.project_node = project_node
        self.project_path = Path(project_node.path)
        self.manager = scope_manager
        self.jedi_manager = jedi_manager

        self.folder_processor = FolderProcessor(project_node, scope_manager)
        self.file_processor = FileProcessor(project_node, scope_manager)

        self.mro_resolver = MROResolver(jedi_manager)
        self.ast_processor = ASTProcessor(scope_manager, self.mro_resolver)

    def reset_session(self) -> None:
        """Reset builder caches between orchestrator runs."""
        self.folder_processor.reset_session()

    async def sync_structure(
        self, change_set: ChangeSet, scan_result: ScanResult, batch_size: int = 100
    ) -> List[FolderChange]:
        """
        Phase 1.5: Batch synchronize all folder and file structures (shells).
        Returns folder changes for notification/logging.
        """
        # 1. Sync Folders
        folder_changes = await self.folder_processor.process_batch(change_set, batch_size=batch_size)

        # 2. Sync Files (Shells)
        await self.file_processor.process_batch(change_set, scan_result, batch_size=batch_size)

        return folder_changes

    async def process_file(
        self, file_path: str, checksum: str
    ) -> Optional[CollectionResult]:
        """
        Process a single file for Phase 2 collection (Content/AST).
        Assumes file scope structure is already synced in Phase 1.5.

        Returns:
        - file_scope: The file scope node
        - removed_scope_ids: IDs of deleted scopes
        - folder_changes: Empty list (kept for signature compatibility or legacy bubbling)
        """
        abs_path = Path(file_path)
        try:
            rel_path = abs_path.relative_to(self.project_path)
        except ValueError:
            logger.error(
                "File %s is not inside project path %s",
                file_path,
                self.project_path,
            )
            return None

        # 1. Retrieve File Scope (Optimized: Should exist from batch sync)
        # We need the ID to process children.
        # We could optimize by having a cache or passing ID, but lookup by path is fast enough for now.
        # However, file_path in DB might not be updated if we rely on qname?
        # FileProcessor updates file_path in DB.

        # We can search by file_path.
        # TODO: Potential race condition if two files map to same path? Unlikely in this flow.
        file_scope_list = await self.manager.get_scopes_by_file_path(str(abs_path))
        if not file_scope_list:
            logger.error(
                f"File scope not found for {file_path} after structure sync")
            return None

        # If multiple scopes return (shouldn't happen for file type), pick the FILE one
        file_scope = next(
            (s for s in file_scope_list if s.type == "file"), None)
        # If types are enums in DB, handle accordingly. ScopeType.FILE is "file".
        if not file_scope:
            # Fallback: maybe just take the first one?
            file_scope = file_scope_list[0]

        # 2. Parse Content & Scan AST
        try:
            async with aiofiles.open(
                str(abs_path), "r", encoding="utf-8"
            ) as f:
                content = await f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None

        # 3. Get existing children from database
        loop = asyncio.get_event_loop()
        try:
            ast_nodes = await loop.run_in_executor(
                None, scan, content, str(abs_path)
            )
        except Exception as e:
            logger.error(
                f"Failed to scan AST for {file_path}: {e}")
            return None

        existing_map = await self._collect_all_descendant_scopes(file_scope.id)

        # 4. Process AST Nodes to build current scope hierarchy
        current_scopes_nodes = await self.ast_processor.process_ast_nodes(
            ast_nodes, file_scope, content)

        # 5. Determine which scopes are new or modified (Internal Update)
        current_ids = set()

        for scope, node in current_scopes_nodes:
            current_ids.add(scope.id)
            existing = existing_map.get(scope.id)
            if not existing:
                logger.debug(f"New scope detected: {scope.qname}")
            else:
                if self._scope_changed(existing, scope):
                    logger.debug(f"Modified scope detected: {scope.qname}")

        # 6. Identify removed scopes
        removed_scope_ids = []
        for child_id in existing_map.keys():
            if child_id not in current_ids:
                removed_scope_ids.append(child_id)
                logger.info(
                    f"Scope removed: {existing_map[child_id].qname} "
                    f"(ID: {child_id})")
        logger.info(
            f"File {file_path}: {len(removed_scope_ids)} scopes removed")

        return CollectionResult(
            file_scope=file_scope,
            removed_scope_ids=removed_scope_ids,
            folder_changes=[],  # Folder changes are now handled in batch sync
        )

    async def process_folder(
        self, folder_path: str
    ) -> Optional[List[FolderChange]]:
        """Ensure folder hierarchy exists for a folder change event."""
        abs_path = Path(folder_path)
        try:
            rel_path = abs_path.relative_to(self.project_path)
        except ValueError:
            logger.error(
                "Folder %s is not inside project path %s",
                folder_path,
                self.project_path,
            )
            return []
        build_result = await self.folder_processor.ensure_folder(rel_path)
        if not build_result:
            return []
        return build_result.folder_changes

    # Delegate to HierarchyBuilder (deprecated) or use new methods?
    # process_folder_changes_batch is now on FolderProcessor.
    async def process_folder_changes_batch(
        self, change_set: ChangeSet, batch_size: int = 100
    ) -> List[FolderChange]:
        return await self.folder_processor.process_batch(change_set, batch_size)

    async def _collect_all_descendant_scopes(
        self, parent_scope_id: str
    ) -> dict[str, ScopeModel]:
        """
        Recursively collect all descendant scopes from a parent scope.
        Returns a dictionary mapping scope ID to ScopeModel.
        """
        result = {}
        queue = [parent_scope_id]

        while queue:
            current_id = queue.pop(0)
            children = await self.manager.get_children(current_id)
            for child in children:
                if child.id not in result:
                    result[child.id] = child
                    queue.append(child.id)

        return result

    def _scope_changed(
        self, existing: ScopeModel, current: ScopeModel
    ) -> bool:
        """
        Check if a scope has changed by comparing key attributes.
        """
        return (
            existing.checksum != current.checksum or
            existing.start_line != current.start_line or
            existing.start_col != current.start_col or
            existing.end_line != current.end_line or
            existing.end_col != current.end_col or
            existing.name != current.name or
            existing.qname != current.qname
        )
