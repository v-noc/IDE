import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import aiofiles
from app.core.model.nodes import ProjectNode, FileNode
from app.core.parser.drivers import DriverManager
from app.core.repository import Repositories
from app.core.parser.graph_builder.discovery.change_detector import ChangeSet
from app.core.parser.graph_builder.discovery.scanner import ScanResult

from .ast_processor import ASTProcessor
from .folder_processor import FolderProcessor, FolderChange
from .file_processor import FileProcessor
from .structure_batch import StructureBatchPlan
from app.core.model.schemas.structure_schema import _code_content_id_for_file
from app.core.parser.graph_builder.performance import tracker

logger = logging.getLogger(__name__)


@dataclass
class CollectionResult:
    structure_batch_plan: "StructureBatchPlan"
    file_node: Optional[FileNode] = None  # For Phase 2 when structure changed
    # File content for CodeContent insert and Phase 2 reuse
    content: Optional[str] = None


class Collector:
    def __init__(
        self,
        project_node: ProjectNode,
        repos: Repositories,
        driver_manager: DriverManager,
    ):
        self.project_node = project_node
        self.project_path = Path(project_node.path)
        self.repos = repos
        self.driver_manager = driver_manager

        self.folder_processor = FolderProcessor(
            project_node)
        self.file_processor = FileProcessor(
            project_node)

        self.ast_processor = ASTProcessor(repos)

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

            # Include CodeContent deletes for deleted files
            content_delete_ids = [
                _code_content_id_for_file(fid)
                for fid in folder_plan.delete
                if "FileSchema" in fid or str(fid).startswith("FileSchema/")
            ]
            all_delete = list(folder_plan.delete) + content_delete_ids

            await self.repos.structure_repo.flush_batch(
                folder_plan.insert,
                [],
                all_delete,
                folder_plan.move,
            )

            await self.repos.structure_repo.update_batch(folder_plan.update)

    async def process_file(
        self, file_node: FileNode, checksum: str, progress_tracker=None
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

            # 3. Parse via language driver (inject IDs + AST + optional MRO)
            try:
                with tracker.timer("collector.process_file.scan_ast"):
                    driver = await self.driver_manager.get_driver(
                        str(abs_path)
                    )
                    parse_result = await driver.parse_file(
                        str(abs_path), content, resolve_mro=True
                    )

                    ast_nodes = parse_result.nodes

                    processed_content = parse_result.content
            except Exception as e:
                print(
                    f"Failed to scan AST for {file_node.path}: {e}")
                return None

            # 4. Sync Content
            with tracker.timer("collector.process_file.sync_content"):
                try:
                    structure_batch_plan = (
                        await self.ast_processor.sync_content(
                            file_node,
                            ast_nodes,
                            content=processed_content,
                            progress_tracker=progress_tracker,
                        )
                    )
                except Exception:
                    logger.exception(
                        "AST/sync_content failed for %s; skipping file",
                        file_node.path,
                    )
                    return None
                file_node_for_phase2 = (
                    file_node
                    if (
                        structure_batch_plan.insert
                        or structure_batch_plan.update
                    )
                    else None
                )
                return CollectionResult(
                    structure_batch_plan=structure_batch_plan,
                    file_node=file_node_for_phase2,
                    content=processed_content,
                )
