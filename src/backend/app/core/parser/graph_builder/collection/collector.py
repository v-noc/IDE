import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import aiofiles
import asyncio
from app.core.model.nodes import ProjectNode, FileNode
from app.core.parser.ast.scanner import scan
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.parser.jedi_adapter.resolver import MROResolver
from app.core.repository import Repositories
from app.core.parser.graph_builder.discovery.change_detector import ChangeSet
from app.core.parser.graph_builder.discovery.scanner import ScanResult

from .ast_processor import ASTProcessor
from .folder_processor import FolderProcessor, FolderChange
from .file_processor import FileProcessor
from app.core.parser.graph_builder.performance import tracker

logger = logging.getLogger(__name__)


@dataclass
class CollectionResult:
    file_node: FileNode
    removed_scope_ids: List[str]  # IDs of scopes that were deleted
    folder_changes: List[FolderChange]


class Collector:
    def __init__(
        self,
        project_node: ProjectNode,
        repos: Repositories,
        jedi_manager: JediProjectManager,
    ):
        self.project_node = project_node
        self.project_path = Path(project_node.path)
        self.repos = repos
        self.jedi_manager = jedi_manager

        self.folder_processor = FolderProcessor(
            project_node)
        self.file_processor = FileProcessor(
            project_node)

        self.mro_resolver = MROResolver(jedi_manager)
        self.ast_processor = ASTProcessor(repos, self.mro_resolver)

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

            folder_plan = self.folder_processor.prepare_batch(
                change_set
            )

            file_plan = self.file_processor.prepare_batch(
                change_set, scan_result
            )

            folder_plan.extend(file_plan)

            await self.repos.folder_repo.flush_batch(
                folder_plan.insert,
                [],
                folder_plan.delete,
                folder_plan.move,
                project_db_name=self.project_node.db_name,
            )

            await self.repos.folder_repo.update_batch(folder_plan.update, project_db_name=self.project_node.db_name)

    async def process_file(
        self, file_node: FileNode, checksum: str, project_db_name: str, progress_tracker=None
    ) -> Optional[CollectionResult]:
        """
        Process a single file for Phase 2 collection (Content/AST).
        Assumes file node structure is already synced in Phase 1.5.

        Returns:
        - file_node: The file node
        - removed_scope_ids: IDs of deleted scopes (handled internally)
        - folder_changes: Empty list (kept for signature compatibility)
        """
        with tracker.timer("collector.process_file_total"):
            abs_path = Path(file_node.path)
            try:
                # Check if file is inside project path
                abs_path.relative_to(self.project_path)
            except ValueError:
                logger.error(
                    "File %s is not inside project path %s",
                    file_node.path,
                    self.project_path,
                )
                return None

            # 2. Parse Content & Scan AST
            try:
                async with aiofiles.open(
                    str(abs_path), "r", encoding="utf-8"
                ) as f:
                    content = await f.read()
            except Exception as e:
                logger.error(f"Failed to read file {file_node.path}: {e}")
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
                    f"Failed to scan AST for {file_node.path}: {e}")
                return None

            # 4. Sync Content
            with tracker.timer("collector.process_file.sync_content"):
                return await self.ast_processor.sync_content(
                    file_node, ast_nodes, project_db_name=project_db_name,   content=processed_content, progress_tracker=progress_tracker
                )
