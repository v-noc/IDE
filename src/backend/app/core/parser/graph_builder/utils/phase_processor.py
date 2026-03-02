"""Processes collection and analysis phases."""
from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import List
import asyncio

from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.analysis.body_parser import BodyParser
from app.core.parser.graph_builder.collection.collector import Collector
from app.core.parser.graph_builder.discovery.change_detector import ChangeSet
from app.core.parser.graph_builder.discovery.scanner import ScanResult
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.repository import Repositories
from app.core.parser.graph_builder.performance import tracker

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
            tp.path
            for tp in (change_set.new_files + change_set.modified_files)
            if tp.path
        ]
        files_to_process.extend(
            [mv.new_path for mv in change_set.moved_files if mv.new_path])

        results = []
        removed_scope_ids = set()

        async def _process_single_file(file_path: str):
            async with self._file_semaphore:
                checksum = scan_result.files.get(file_path)
                if not checksum:
                    return None
                logger.info(f"Collecting structure for: {file_path}")
                # Set current file at start of processing
                if progress_tracker:
                    progress_tracker.set_current_file(file_path)
                    await progress_tracker.emit()
                try:
                    result = await asyncio.wait_for(
                        self.collector.process_file(
                            file_path, checksum, project_db_name=self.project_node.db_name, progress_tracker=progress_tracker),
                        timeout=self._file_timeout,
                    )
                    # Update file progress
                    if progress_tracker:
                        progress_tracker.increment_file_processed(file_path)
                        await progress_tracker.emit()
                    return result
                except Exception as exc:
                    logger.error(
                        "Error in collector.process_file for %s: %s",
                        file_path, exc
                    )
                    # Still update progress even on error
                    if progress_tracker:
                        progress_tracker.increment_file_processed(file_path)
                        await progress_tracker.emit()
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
        async def _process_single_file_analysis(result):
            """Process a single file's AST analysis."""
            body_parser = BodyParser(
                self.project_node,
                self.repos,
                self.jedi_manager,
                batch_size=self._batch_size,
                progress_tracker=progress_tracker,
            )

            with tracker.timer("phase2.analyze_file"):
                async with self._file_semaphore:
                    try:
                        logger.info(
                            "Analyzing call graph for: %s",
                            result.file_node.qname,
                        )

                        # Set current file at start of processing
                        if progress_tracker:
                            progress_tracker.set_current_file(
                                result.file_node.path)
                            await progress_tracker.emit()

                        # NOTE: Do NOT delete descendant calls here.
                        # The BodyParser -> CallChainBuilder -> ScopeProcessor
                        # will handle "Diffing" (Create/Keep/Delete) per function scope.

                        # Process AST
                        with tracker.timer("phase2.process_ast"):
                            await asyncio.wait_for(
                                body_parser.process_ast(result.file_node),
                                timeout=self._file_timeout,
                            )

                        # Clear current function when file is done
                        if progress_tracker:
                            progress_tracker.clear_current_function()

                        # Update file progress
                        if progress_tracker:
                            progress_tracker.increment_file_processed(
                                result.file_node.path)
                            await progress_tracker.emit()

                    except Exception as exc:
                        logger.error(
                            f"Error analyzing file {result.file_node.path}: {exc}",
                            exc_info=True
                        )
                        # Still update progress even on error
                        if progress_tracker:
                            progress_tracker.increment_file_processed(
                                result.file_node.path)
                            await progress_tracker.emit()

        # Execute in parallel
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(_process_single_file_analysis(result))
                for result in collection_results
            ]

        for task in tasks:
            task.result()
