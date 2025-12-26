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
from app.core.parser.scope_manager.models import ScopeModel, ScopeType
from app.core.parser.graph_builder.discovery.change_detector import ChangeSet
from app.core.parser.graph_builder.discovery.scanner import ScanResult

from .ast_processor import ASTProcessor
from .folder_processor import FolderProcessor, FolderChange
from .file_processor import FileProcessor
from app.core.parser.graph_builder.performance import tracker

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
        self,
        change_set: ChangeSet,
        scan_result: ScanResult,
        batch_size: int = 100
    ) -> List[FolderChange]:
        """
        Phase 1.5: Batch synchronize all folder and file structures (shells).
        Returns folder changes for notification/logging.
        """
        with tracker.timer("collector.sync_structure"):
            # 1. Sync Folders
            with tracker.timer("collector.sync_folders"):
                folder_changes = await self.folder_processor.process_batch(
                    change_set, batch_size=batch_size
                )

            # 2. Sync Files (Shells)
            with tracker.timer("collector.sync_files_shells"):
                await self.file_processor.process_batch(
                    change_set, scan_result, batch_size=batch_size
                )

            return folder_changes

    async def process_file(
        self, file_path: str, checksum: str
    ) -> Optional[CollectionResult]:
        """
        Process a single file for Phase 2 collection (Content/AST).
        Assumes file scope structure is already synced in Phase 1.5.

        Returns:
        - file_scope: The file scope node
        - removed_scope_ids: IDs of deleted scopes (handled internally)
        - folder_changes: Empty list (kept for signature compatibility)
        """
        with tracker.timer("collector.process_file_total"):
            abs_path = Path(file_path)
            try:
                # Check if file is inside project path
                abs_path.relative_to(self.project_path)
            except ValueError:
                logger.error(
                    "File %s is not inside project path %s",
                    file_path,
                    self.project_path,
                )
                return None

            # 1. Retrieve File Scope (Optimized: Should exist from batch sync)
            with tracker.timer("collector.process_file.get_scope"):
                file_scope_list = await self.manager.get_scopes_by_file_path(
                    str(abs_path)
                )
            if not file_scope_list:
                logger.error(
                    f"File scope not found for {file_path} after "
                    f"structure sync"
                )
                return None

            # If multiple scopes return (shouldn't happen for file type),
            # pick the FILE one
            file_scope = next(
                (s for s in file_scope_list if s.type == ScopeType.FILE),
                file_scope_list[0]
            )

            # 2. Parse Content & Scan AST
            try:
                async with aiofiles.open(
                    str(abs_path), "r", encoding="utf-8"
                ) as f:
                    content = await f.read()
            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {e}")
                return None

            # 3. Scan AST
            loop = asyncio.get_event_loop()
            try:
                # scan now returns (nodes, processed_content)
                with tracker.timer("collector.process_file.scan_ast"):
                    ast_nodes, processed_content = await loop.run_in_executor(
                        None, scan, content, str(abs_path)
                    )
            except Exception as e:
                logger.error(
                    f"Failed to scan AST for {file_path}: {e}")
                return None

            # 4. Sync Content
            # This handles fetching descendants, diffing, and batch DB ops
            # (Create/Update/Delete/Relink). Use processed_content because
            # line numbers in ast_nodes match it (IDs injected)
            with tracker.timer("collector.process_file.sync_content"):
                await self.ast_processor.sync_content(
                    file_scope, ast_nodes, processed_content
                )

            return CollectionResult(
                file_scope=file_scope,
                removed_scope_ids=[],  # Deletions handled internally
                folder_changes=[],
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

    async def process_folder_changes_batch(
        self, change_set: ChangeSet, batch_size: int = 100
    ) -> List[FolderChange]:
        return await self.folder_processor.process_batch(
            change_set, batch_size
        )
