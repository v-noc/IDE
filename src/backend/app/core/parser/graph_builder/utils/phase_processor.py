"""Processes collection and analysis phases."""
from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import List
import asyncio

from app.core.model.nodes import FileNode, ProjectNode
from app.core.parser.graph_builder.analysis.body_parser import BodyParser
from app.core.parser.graph_builder.collection.collector import Collector
from app.core.parser.graph_builder.discovery.change_detector import ChangeSet
from app.core.parser.graph_builder.discovery.scanner import ScanResult
from app.core.parser.jedi_adapter.manager import JediProjectManager
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
        jedi_manager: JediProjectManager,
        max_concurrent_files: int = 50,
        max_concurrent_db: int = 100,
        file_timeout: float = 10*60.0,
        batch_size: int = 100,
    ):
        self.project_node = project_node
        self.project_path = project_path
        self.repos = repos
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
                    return None, None
                logger.info(f"Collecting structure for: {file_node.path}")
                # Set current file at start of processing
                if progress_tracker:
                    progress_tracker.set_current_file(file_node.path)
                    await progress_tracker.emit()
                try:

                    result = await asyncio.wait_for(
                        self.collector.process_file(
                            file_node, checksum, project_db_name=self.project_node.db_name, progress_tracker=progress_tracker),
                        timeout=self._file_timeout,
                    )

                    # Update file progress
                    if progress_tracker:
                        progress_tracker.increment_file_processed(
                            file_node.path)
                        await progress_tracker.emit()
                    for tp in (change_set.new_files + change_set.modified_files):
                        if file_node.id == tp.id:
                            if len(result.insert) > 0 or len(result.update) > 0:
                                return result, file_node

                    return result, None
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
                    return None, None

        file_nodes = await self.repos.file_repo.get_by_ids(files_to_process, project_db_name=self.project_node.db_name)
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(_process_single_file(node))
                for node in file_nodes
            ]

        structure_batch_plan = StructureBatchPlan()
        results = []
        for task in tasks:
            result, file_node = task.result()
            if result:
                structure_batch_plan.extend(result)
            if file_node:
                results.append(file_node)

        await self.repos.file_repo.flush_batch(
            structure_batch_plan.insert,
            [],
            structure_batch_plan.delete,
            structure_batch_plan.move,
            project_db_name=self.project_node.db_name,
        )
        await self.repos.function_repo.update_batch(structure_batch_plan.update, project_db_name=self.project_node.db_name)

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
            self.jedi_manager,
            batch_size=5000,
            progress_tracker=progress_tracker,
        )

        async def _process_single_file_analysis(file_node: FileNode):
            """Process a single file's AST analysis."""

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

                        # Process AST
                        with tracker.timer("phase2.process_ast"):
                            await asyncio.wait_for(
                                body_parser.process_ast(file_node),
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

        # Execute in parallel
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(_process_single_file_analysis(file_node))
                for file_node in collection_results
            ]

        for task in tasks:
            task.result()

        # Flush all buffered call operations (inserts, deletes, moves) in one final batch
        await body_parser.flush_buffers()
