"""Processes collection and analysis phases."""
from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import List
import asyncio

from app.core.model.nodes import FileNode, ProjectNode
from app.core.parser.graph_builder.analysis.body_parser import BodyParser
from app.core.parser.graph_builder.collection.collector import Collector, CollectionResult
from app.core.parser.graph_builder.discovery.change_detector import ChangeSet
from app.core.parser.graph_builder.discovery.scanner import ScanResult
from app.core.parser.drivers import DriverManager
from app.core.repository import Repositories
from app.core.parser.graph_builder.performance import tracker
from app.core.parser.graph_builder.collection.structure_batch import StructureBatchPlan

logger = logging.getLogger(__name__)


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
        repos: Repositories,
        collector: Collector,
        driver_manager: DriverManager,
        max_concurrent_files: int = 50,
        max_concurrent_db: int = 100,
        file_timeout: float = 10*60.0,
        batch_size: int = 100,
    ):
        self.project_node = project_node
        self.project_path = project_path
        self.repos = repos
        self.collector = collector
        self.driver_manager = driver_manager

        # Concurrency control
        self._file_semaphore = asyncio.Semaphore(max_concurrent_files)
        self._db_semaphore = asyncio.Semaphore(max_concurrent_db)
        self._file_timeout = file_timeout
        self._batch_size = batch_size

    async def process_collection_phase(
        self,
        change_set: ChangeSet,
        scan_result: ScanResult,
        progress_tracker=None,
    ) -> List:
        """
        Phase 1: Structure Collection.
        (Code remains unchanged from your snippet, it is correct)
        """
        files_to_process = [
            tp.id
            for tp in (change_set.new_files + change_set.modified_files)
            if tp.id
        ]
        files_to_process.extend(
            [mv.id for mv in change_set.moved_files if mv.id])

        results = []

        async def _process_single_file(file_node: FileNode):
            async with self._file_semaphore:
                checksum = scan_result.files.get(file_node.path)
                if not checksum:
                    return None
                logger.info(f"Collecting structure for: {file_node.path}")
                # Set current file at start of processing
                if progress_tracker:
                    progress_tracker.set_current_file(file_node.path)
                    await progress_tracker.emit()
                try:
                    print(f"processing file: {file_node.path}")
                    result = await asyncio.wait_for(
                        self.collector.process_file(
                            file_node, checksum, progress_tracker=progress_tracker),
                        timeout=self._file_timeout,
                    )

                    # Update file progress
                    if progress_tracker:
                        progress_tracker.increment_file_processed(
                            file_node.path)
                        await progress_tracker.emit()
                    return (result, file_node)
                except Exception as exc:
                    logger.error(
                        "Error in collector.process_file for %s: %s",
                        file_node.path, exc
                    )
                    # Still update progress even on error
                    if progress_tracker:
                        progress_tracker.increment_file_processed(
                            file_node.path)
                        await progress_tracker.emit()
                    return None

        file_nodes = await self.repos.structure_repo.get_by_ids(files_to_process)
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(_process_single_file(node))
                for node in file_nodes
            ]

        structure_batch_plan = StructureBatchPlan()
        results = []  # (file_node, content) for Phase 2
        content_inserts = []  # (file_id, content) for new files
        content_updates = []  # (file_id, content) for modified files

        for task in tasks:
            task_result = task.result()
            if task_result is None:
                continue
            result, file_node = task_result
            if result is None:
                continue
            structure_batch_plan.extend(result.structure_batch_plan)
            if result.file_node:
                results.append((result.file_node, result.content))
            if result.content and file_node:
                file_id = file_node.id
                is_new = any(tp.id == file_id for tp in change_set.new_files)
                if is_new:
                    content_inserts.append((file_id, result.content))
                else:
                    content_updates.append((file_id, result.content))

        await self.repos.code_element_repo.flush_batch(
            structure_batch_plan.insert,
            structure_batch_plan.update,
            content_inserts + content_updates,
            structure_batch_plan.delete,
            structure_batch_plan.move,
        )
        # await self.repos.code_element_repo.update_batch(structure_batch_plan.update)

        # Batch insert/update CodeContent (extends flush pattern, single API call)
        # await self.repos.structure_repo.flush_content_batch(content_inserts, content_updates)

        # Return (file_node, content) for Phase 2 to avoid duplicate file reads
        return results

    async def process_analysis_phase(
        self,
        collection_results: List,
        progress_tracker=None,
    ) -> None:
        """
        Phase 2: Body Analysis (Calls).

        Orchestrates the BodyParser which uses the CallChainBuilder.
        """
        body_parser = BodyParser(
            self.project_node,
            self.repos,
            self.driver_manager,
            batch_size=5000,
            progress_tracker=progress_tracker,
        )

        async def _process_single_file_analysis(file_node: FileNode, content: str | None = None):
            """Process a single file's AST analysis. Pass content to avoid duplicate file read."""

            with tracker.timer("phase2.analyze_file"):
                async with self._file_semaphore:
                    try:
                        logger.info(
                            "Analyzing call graph for: %s",
                            file_node.qname,
                        )

                        # Set current file at start of processing
                        if progress_tracker:
                            progress_tracker.set_current_file(
                                file_node.path)
                            await progress_tracker.emit()

                        # Process AST (content from Phase 1 avoids duplicate file read)
                        with tracker.timer("phase2.process_ast"):
                            await asyncio.wait_for(
                                body_parser.process_ast(
                                    file_node, content=content),
                                timeout=self._file_timeout,
                            )

                        # Clear current function when file is done
                        if progress_tracker:
                            progress_tracker.clear_current_function()

                        # Update file progress
                        if progress_tracker:
                            progress_tracker.increment_file_processed(
                                file_node.path)
                            await progress_tracker.emit()

                    except Exception as exc:
                        logger.error(
                            f"Error analyzing file {file_node.path}: {exc}",
                            exc_info=True
                        )
                        # Still update progress even on error
                        if progress_tracker:
                            progress_tracker.increment_file_processed(
                                file_node.path)
                            await progress_tracker.emit()

        # Execute in parallel (collection_results are (file_node, content) tuples)
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(_process_single_file_analysis(fn, content))
                for fn, content in collection_results
            ]

        for task in tasks:
            task.result()

        # Flush all buffered call operations (inserts, deletes, moves) in one final batch
        await body_parser.flush_buffers()
