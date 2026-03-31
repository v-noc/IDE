"""Processes collection and analysis phases."""
from dataclasses import dataclass, field
import logging
from typing import List, Tuple
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

# Default cap for UTF-8 size of file contents per TerminusDB commit (payload safety).
_DEFAULT_MAX_CONTENT_BYTES_PER_FLUSH = 4 * 1024 * 1024


def _chunk_file_content_pairs(
    pairs: List[Tuple[str, str]],
    max_items: int,
    max_bytes: int,
) -> List[List[Tuple[str, str]]]:
    """Split (file_id, content) pairs so each chunk is bounded by count and UTF-8 byte size."""
    if not pairs:
        return []
    chunks: List[List[Tuple[str, str]]] = []
    current: List[Tuple[str, str]] = []
    cur_bytes = 0
    for _fid, text in pairs:
        b = len(text.encode("utf-8"))
        if current:
            over_items = len(current) >= max_items
            # New chunk if adding would exceed byte budget, unless this row alone exceeds max_bytes
            over_bytes = cur_bytes + b > max_bytes and b <= max_bytes
            if over_items or over_bytes:
                chunks.append(current)
                current = []
                cur_bytes = 0
        current.append((_fid, text))
        cur_bytes += b
    if current:
        chunks.append(current)
    return chunks


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
        batch_size: int = 4000,
        max_content_bytes_per_flush: int = _DEFAULT_MAX_CONTENT_BYTES_PER_FLUSH,
        max_queries_per_code_flush: int = 2000,
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
        self._max_content_bytes_per_flush = max_content_bytes_per_flush
        self._max_queries_per_code_flush = max_queries_per_code_flush

    async def _flush_code_element_buffer(
        self,
        buffer: List[Tuple[CollectionResult, FileNode]],
        change_set: ChangeSet,
    ) -> None:
        """Merge a batch of collection results and flush to TerminusDB (bounded payload)."""
        if not buffer:
            return
        structure_batch_plan = StructureBatchPlan()
        content_inserts: List[Tuple[str, str]] = []
        content_updates: List[Tuple[str, str]] = []
        for result, file_node in buffer:
            structure_batch_plan.extend(result.structure_batch_plan)
            if result.content and file_node:
                file_id = file_node.id
                is_new = any(tp.id == file_id for tp in change_set.new_files)
                if is_new:
                    content_inserts.append((file_id, result.content))
                else:
                    content_updates.append((file_id, result.content))

        content_pairs = content_inserts + content_updates
        has_structure = bool(
            structure_batch_plan.insert
            or structure_batch_plan.update
            or structure_batch_plan.delete
            or structure_batch_plan.move
        )
        if not has_structure and not content_pairs:
            return

        logger.info(
            "Code DB flush: scope_insert=%d scope_update=%d scope_delete=%d "
            "move=%d code_content_rows=%d",
            len(structure_batch_plan.insert),
            len(structure_batch_plan.update),
            len(structure_batch_plan.delete),
            len(structure_batch_plan.move),
            len(content_pairs),
        )

        # content_chunks = _chunk_file_content_pairs(
        #     content_pairs,
        #     max_items=max(1, self._batch_size),
        #     max_bytes=max(1, self._max_content_bytes_per_flush),
        # )
        # if not content_chunks:
        #     content_chunks = [[]]

        await self.repos.code_element_repo.flush_batch(
            structure_batch_plan.insert,
            structure_batch_plan.update,
            content_pairs,
            structure_batch_plan.delete,
            structure_batch_plan.move,
            max_queries_per_commit=self._max_queries_per_code_flush,
        )

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
        tasks = [
            asyncio.create_task(_process_single_file(node))
            for node in file_nodes
        ]

        results: List = []  # (file_node, content) for Phase 2
        pending: List[Tuple[CollectionResult, FileNode]] = []

        for done in asyncio.as_completed(tasks):
            task_result = await done
            if task_result is None:
                continue
            result, file_node = task_result
            if result is None:
                continue
            if result.file_node:
                results.append((result.file_node, result.content))
            pending.append((result, file_node))
            if len(pending) >= self._batch_size:
                await self._flush_code_element_buffer(pending, change_set)
                pending.clear()

        if pending:
            await self._flush_code_element_buffer(pending, change_set)

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
            batch_size=self._batch_size,
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
