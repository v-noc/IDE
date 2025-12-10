"""Processes collection and analysis phases."""
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

logger = logging.getLogger(__name__)

# Timeout for individual file processing (in seconds)
FILE_PROCESSING_TIMEOUT = 60  # 1 minute per file
# Limit workers to reduce database connection contention
MAX_WORKERS = 4


class PhaseProcessor:
    """Processes collection and analysis phases."""

    def __init__(
        self,
        project_node: ProjectNode,
        project_path: str,
        scope_manager: ScopeManager,
        collector: Collector,
        jedi_manager: JediProjectManager,
        batch_size: int = 500,
    ):
        self.project_node = project_node
        self.project_path = project_path
        self.scope_manager = scope_manager
        self.collector = collector
        self.jedi_manager = jedi_manager
        self.batch_size = batch_size

    def process_collection_phase(
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

        collection_results = []
        removed_scope_ids_to_delete = []

        def _process_single_file(file_path: str):
            checksum = scan_result.files.get(file_path)
            if not checksum:
                return None
            logger.info(f"Collecting structure for: {file_path}")
            try:
                return self.collector.process_file(file_path, checksum)
            except Exception as exc:
                # Log error but don't let it propagate to avoid deadlocks
                logger.error(
                    "Error in collector.process_file for %s: %s",
                    file_path,
                    exc,
                    exc_info=True,
                )
                return None

        # Run file collection in parallel to improve throughput
        # Limit workers to reduce database connection contention
        with ThreadPoolExecutor() as executor:
            future_to_file = {
                executor.submit(_process_single_file, file_path): file_path
                for file_path in files_to_process
            }
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    # Add timeout to prevent indefinite hanging
                    result = future.result(timeout=FILE_PROCESSING_TIMEOUT)
                except FutureTimeoutError:
                    logger.error(
                        "Timeout collecting structure for %s (exceeded %d seconds)",
                        file_path,
                        FILE_PROCESSING_TIMEOUT,
                    )
                    continue
                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.error(
                        "Error collecting structure for %s: %s",
                        file_path,
                        exc,
                        exc_info=True,
                    )
                    continue

                if result:
                    collection_results.append(result)
                    # Collect removed scope IDs to delete after parallel processing
                    removed_scope_ids_to_delete.extend(
                        result.removed_scope_ids)

        # Delete Removed Scopes sequentially after all parallel work is done
        # This avoids race conditions and database connection contention
        for scope_id in removed_scope_ids_to_delete:
            try:
                logger.info("Deleting removed scope ID: %s", scope_id)
                self.scope_manager.delete_scope(scope_id)
            except Exception as exc:
                logger.error(
                    "Error deleting scope ID %s: %s",
                    scope_id,
                    exc,
                    exc_info=True,
                )
                # Continue with other deletions even if one fails

        return collection_results

    def process_analysis_phase(
        self,
        collection_results: List,
        call_sync_service: Optional[Callable[[List[str]], None]] = None,
    ) -> None:
        """
        Process Phase 2: Body Analysis (Calls).

        Args:
            collection_results: Results from collection phase
            call_sync_service: Optional service to sync call chains after analysis
        """
        def _process_single_file_analysis(result):
            """Process a single file's AST analysis in a thread."""
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
                self.scope_manager.clear_calls(result.file_scope.id)

                # Parse the full AST tree
                # BodyParser traverses descendants and clears their calls en route
                body_parser.process_ast(result.file_scope)

                # Flush any remaining call sites in the buffer for this file
                processed_scope_ids = body_parser.flush_all_call_sites()

                # Get stats from this file's processing
                stats = body_parser.get_stats()

                return {
                    "processed_scope_ids": processed_scope_ids,
                    "stats": stats,
                }
            except Exception as exc:
                print(
                    f"Error processing file {result.file_scope.file_path}: {exc}")
                return None

        # Run file analysis in parallel threads
        # Limit workers to reduce database connection contention
        start_time = time.time()
        finshed = 0

        # Aggregate statistics across all files
        total_resolve_call_count = 0
        total_resolve_call_time = 0.0
        total_get_scope_count = 0
        total_get_scope_time = 0.0

        sync_executor = ThreadPoolExecutor(max_workers=1)

        with ThreadPoolExecutor() as executor:
            future_to_result = {
                executor.submit(_process_single_file_analysis, result): result
                for result in collection_results
            }
            for future in as_completed(future_to_result):
                result = future_to_result[future]
                finshed += 1

                try:
                    # Add timeout to prevent indefinite hanging
                    file_result = future.result(
                        timeout=FILE_PROCESSING_TIMEOUT)

                    if file_result:
                        processed_scope_ids = file_result.get(
                            "processed_scope_ids")
                        stats = file_result.get("stats", {})

                        # Aggregate statistics
                        total_resolve_call_count += stats.get(
                            "resolve_call_count", 0)
                        total_resolve_call_time += stats.get(
                            "resolve_call_time", 0.0)
                        total_get_scope_count += stats.get(
                            "get_scope_count", 0)
                        total_get_scope_time += stats.get(
                            "get_scope_time", 0.0)

                        # Run sync immediately after processing this file
                        if call_sync_service and processed_scope_ids:
                            logger.info(
                                "Syncing call chains for %d processed scopes from file %s",
                                len(processed_scope_ids),
                                result.file_scope.file_path,
                            )
                            try:
                                sync_executor.submit(
                                    call_sync_service, list(processed_scope_ids))
                            except Exception as sync_exc:
                                print(
                                    "Error syncing call chains for file %s: %s",
                                    result.file_scope.file_path,
                                    sync_exc,
                                    exc_info=True,
                                )

                        # Calculate elapsed time and averages
                        elapsed_time = time.time() - start_time
                        avg_time_per_result = elapsed_time / finshed if finshed > 0 else 0.0
                        avg_resolve_time = total_resolve_call_time / \
                            total_resolve_call_count if total_resolve_call_count > 0 else 0.0
                        avg_get_scope_time = total_get_scope_time / \
                            total_get_scope_count if total_get_scope_count > 0 else 0.0

                        print(
                            f"Finished {finshed} of {len(collection_results)} | "
                            f"Total time: {elapsed_time:.2f}s | "
                            f"Avg time/result: {avg_time_per_result:.3f}s | "
                            f"Resolve calls: {total_resolve_call_count} (avg: {avg_resolve_time:.4f}s) | "
                            f"Get scope calls: {total_get_scope_count} (avg: {avg_get_scope_time:.4f}s)"
                        )

                except FutureTimeoutError:
                    print(
                        "Timeout analyzing file %s (exceeded %d seconds)",
                        result.file_scope.file_path,
                        FILE_PROCESSING_TIMEOUT,
                    )
                    continue
                except Exception as exc:  # pragma: no cover - defensive logging
                    print(
                        "Error analyzing file %s: %s",
                        result.file_scope.file_path,
                        exc,
                        exc_info=True,
                    )
                    continue

        # Ensure all threads have completed
        # The ThreadPoolExecutor context manager should handle this, but be explicit
        logger.debug("Waiting for all analysis threads to complete...")
        sync_executor.shutdown(wait=True)
        # Print final summary
        final_time = time.time() - start_time
        final_avg_time = final_time / \
            len(collection_results) if len(collection_results) > 0 else 0.0
        final_avg_resolve = total_resolve_call_time / \
            total_resolve_call_count if total_resolve_call_count > 0 else 0.0
        final_avg_get_scope = total_get_scope_time / \
            total_get_scope_count if total_get_scope_count > 0 else 0.0

        import sys
        print("\n" + "=" * 80, flush=True)
        print("ANALYSIS PHASE SUMMARY", flush=True)
        print("=" * 80, flush=True)
        print(f"Total files processed: {finshed}", flush=True)
        print(f"Total time: {final_time:.2f}s", flush=True)
        print(f"Average time per file: {final_avg_time:.3f}s", flush=True)
        print(f"Total resolve calls: {total_resolve_call_count}", flush=True)
        print(
            f"Total resolve call time: {total_resolve_call_time:.4f}s", flush=True)
        print(
            f"Average resolve call time: {final_avg_resolve:.4f}s", flush=True)
        print(f"Total get scope calls: {total_get_scope_count}", flush=True)
        print(f"Total get scope time: {total_get_scope_time:.4f}s", flush=True)
        print(
            f"Average get scope time: {final_avg_get_scope:.4f}s", flush=True)
        print("=" * 80 + "\n", flush=True)

        logger.info("Analysis phase completed successfully")
