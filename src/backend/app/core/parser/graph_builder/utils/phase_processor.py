"""Processes collection and analysis phases."""
from dataclasses import dataclass, field
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Callable, List, Optional
import time
from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.analysis.body_parser import BodyParser
from app.core.parser.graph_builder.collection.collector import Collector
from app.core.parser.graph_builder.discovery.change_detector import ChangeSet
from app.core.parser.graph_builder.discovery.scanner import ScanResult
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.parser.scope_manager.manager import ScopeManager
import aiofiles
import asyncio

logger = logging.getLogger(__name__)

# Timeout for individual file processing (in seconds)
FILE_PROCESSING_TIMEOUT = 60  # 1 minute per file
# Limit workers to reduce database connection contention
MAX_WORKERS = 4


@dataclass
class ProcessingStats:
    """Statistics for phase processing."""
    files_processed: int = 0
    files_failed: int = 0
    total_time: float = 0.0
    errors: List[tuple] = field(default_factory=list)


class PhaseProcessor:
    """Processes collection and analysis phases."""

    def __init__(
        self,
        project_node: ProjectNode,
        project_path: str,
        scope_manager: ScopeManager,
        collector: Collector,
        jedi_manager: JediProjectManager,
        max_concurrent_files: int = 50,
        max_concurrent_db: int = 100,
        file_timeout: float = 60.0,
        batch_size: int = 100,
    ):
        self.project_node = project_node
        self.project_path = project_path
        self.scope_manager = scope_manager
        self.collector = collector
        self.jedi_manager = jedi_manager

        # Concurrency control
        self._file_semaphore = asyncio.Semaphore(max_concurrent_files)
        self._db_semaphore = asyncio.Semaphore(max_concurrent_db)
        self._file_timeout = file_timeout
        self._batch_size = batch_size

    async def process_collection_phase(
        self,
        change_set: ChangeSet,
        scan_result: ScanResult,
    ) -> List:
        """
        Process Phase 1: Collection (Structure).

        Args:
            change_set: Detected changes
            scan_result: Scan results with file checksums

        Returns:
            List of collection results
        """
        self.collector.reset_session()
        files_to_process = change_set.new_files + change_set.modified_files

        results = []
        removed_scope_ids = []
        folder_changes = []

        async def _process_single_file(file_path: str):
            async with self._file_semaphore:
                checksum = scan_result.files.get(file_path)
                if not checksum:
                    return None
                logger.info(f"Collecting structure for: {file_path}")
                try:
                    result = await asyncio.wait_for(
                        self.collector.process_file(file_path, checksum),
                        timeout=self._file_timeout,
                    )
                    return result
                except Exception as exc:
                    # Log error but don't let it propagate to avoid deadlocks
                    logger.error(
                        "Error in collector.process_file for %s: %s",
                        file_path,
                        exc,
                        exc_info=True,
                    )
                    return None

        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(_process_single_file(file_path))
                for file_path in files_to_process
            ]

        for task in tasks:
            result = task.result()
            if result:
                results.append(result)
                removed_scope_ids.update(result.removed_scope_ids)
                folder_changes.extend(result.folder_changes)

        if removed_scope_ids:
            await self._batch_delete_scopes(list(removed_scope_ids))
        return results

    async def process_analysis_phase(
        self,
        collection_results: List,
        call_sync_service=None,
    ) -> None:
        """
        Process Phase 2: Body Analysis (Calls).

        Args:
            collection_results: Results from collection phase
            call_sync_service: Optional service to sync call chains after analysis
        """

        all_processed_scope_ids = set()

        async def _process_single_file_analysis(result):
            """Process a single file's AST analysis in a thread."""
            async with self._file_semaphore:
                try:
                    logger.info(
                        "Analyzing changes for: %s",
                        result.file_scope.file_path,
                    )

                    # Create a new BodyParser for this thread/file
                    body_parser = BodyParser(
                        self.project_path,
                        self.project_node.name,
                        self.scope_manager,
                        self.jedi_manager,
                        batch_size=self.batch_size,
                    )

                    # Process File Body (Full Analysis)
                    logger.info("Processing file body: %s",
                                result.file_scope.qname)

                    # Clear file-scope calls; children clear during traversal
                    await self.scope_manager.clear_calls(result.file_scope.id)

                    # Process AST
                    await asyncio.wait_for(
                        body_parser.process_ast(result.file_scope),
                        timeout=self._file_timeout,
                    )

                    # Flush any remaining call sites in the buffer for this file
                    processed_scope_ids = await body_parser.flush_all_call_sites()
                    if call_sync_service and processed_scope_ids:
                        await call_sync_service.collect_call_infos(list(processed_scope_ids))

                    return processed_scope_ids
                except Exception as exc:
                    print(
                        f"Error processing file {result.file_scope.file_path}: {exc}")
                    return set()

        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(_process_single_file_analysis(result))
                for result in collection_results
            ]

        for task in tasks:
            processed_scope_ids = task.result()
            all_processed_scope_ids.update(processed_scope_ids)

        return all_processed_scope_ids

    async def _batch_delete_scopes(self, scope_ids: List[str]) -> None:
        """Batch delete scopes with concurrency control."""
        async with self._db_semaphore:
            await self.scope_manager.batch_delete_scopes(scope_ids)
