"""Processes collection and analysis phases."""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Optional

from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.analysis.body_parser import BodyParser
from app.core.parser.graph_builder.collection.collector import Collector
from app.core.parser.graph_builder.discovery.change_detector import ChangeSet
from app.core.parser.graph_builder.discovery.scanner import ScanResult
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.parser.scope_manager.manager import ScopeManager

logger = logging.getLogger(__name__)


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

        def _process_single_file(file_path: str):
            checksum = scan_result.files.get(file_path)
            if not checksum:
                return None
            logger.info(f"Collecting structure for: {file_path}")
            return self.collector.process_file(file_path, checksum)

        # Run file collection in parallel to improve throughput
        with ThreadPoolExecutor() as executor:
            future_to_file = {
                executor.submit(_process_single_file, file_path): file_path
                for file_path in files_to_process
            }
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.error(
                        "Error collecting structure for %s: %s",
                        file_path,
                        exc,
                    )
                    continue

                if result:
                    collection_results.append(result)
                    # Delete Removed Scopes (sequential to avoid races)
                    for scope_id in result.removed_scope_ids:
                        logger.info("Deleting removed scope ID: %s", scope_id)
                        self.scope_manager.delete_scope(scope_id)

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
            logger.info("Processing file body: %s", result.file_scope.qname)

            # Clear file-scope calls; children clear during traversal
            self.scope_manager.clear_calls(result.file_scope.id)

            # Parse the full AST tree
            # BodyParser traverses descendants and clears their calls en route
            body_parser.process_ast(result.file_scope)

            # Flush any remaining call sites in the buffer for this file
            processed_scope_ids = body_parser.flush_all_call_sites()

            return processed_scope_ids

        # Run file analysis in parallel threads
        with ThreadPoolExecutor() as executor:
            future_to_result = {
                executor.submit(_process_single_file_analysis, result): result
                for result in collection_results
            }
            for future in as_completed(future_to_result):
                result = future_to_result[future]

                try:
                    processed_scope_ids = future.result()

                    # Run sync immediately after processing this file
                    if call_sync_service and processed_scope_ids:
                        logger.info(
                            "Syncing call chains for %d processed scopes from file %s",
                            len(processed_scope_ids),
                            result.file_scope.file_path,
                        )
                        call_sync_service(list(processed_scope_ids))

                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.error(
                        "Error analyzing file %s: %s",
                        result.file_scope.file_path,
                        exc,
                    )
                    continue
