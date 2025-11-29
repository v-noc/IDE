import logging
from typing import Optional
from pathlib import Path

from arango.database import StandardDatabase

from app.core.model.nodes import ProjectNode
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.graph_builder.discovery.scanner import FileScanner
from app.core.parser.graph_builder.discovery.change_detector import (
    ChangeDetector,
    ChangeSet,
)

from app.core.parser.graph_builder.collection.collector import Collector
from app.core.parser.graph_builder.analysis.body_parser import BodyParser


logger = logging.getLogger(__name__)


class GraphBuilderOrchestrator:
    def __init__(
        self,
        project_node: ProjectNode,
        db: Optional[StandardDatabase] = None,
        scope_manager: Optional[ScopeManager] = None,
        ignore_file_name: str = ".gitignore",
    ):
        self.project_node = project_node
        self.project_path = project_node.path
        # Main ArangoDB connection (optional for now)
        self.db = db

        # Initialize ScopeManager
        # Note: ScopeManager handles DB connection internally
        self.scope_manager = scope_manager or ScopeManager(project_node.name)

        # Initialize Jedi Adapter
        from app.core.parser.jedi_adapter.manager import JediProjectManager

        self.jedi_manager = JediProjectManager(Path(self.project_path))

        # Initialize Discovery components
        self.file_scanner = FileScanner(
            self.project_path,
            ignore_file_name=ignore_file_name,
        )
        self.change_detector = ChangeDetector(self.scope_manager)

        # Initialize Collection components
        self.collector = Collector(
            self.project_node,
            self.scope_manager,
            self.jedi_manager,
        )

        # Initialize Analysis components
        self.body_parser = BodyParser(
            self.project_path,
            self.project_node.name,
            self.scope_manager,
            self.jedi_manager
        )

    def resync(self) -> ChangeSet:
        """
        Perform an incremental resync of the project.
        1. Scan files
        2. Detect changes
        3. Phase 1: Structure Collection (Scopes)
        4. Phase 2: Body Analysis (Calls)
        """
        logger.info(
            "Starting resync for project: %s",
            self.project_node.name,
        )

        # 1. Scan Disk
        current_files = self.file_scanner.scan()
        logger.info(f"Scanned {len(current_files)} files on disk")

        # 2. Detect Changes
        change_set = self.change_detector.detect_changes(current_files)
        logger.info(f"Detected changes: {change_set}")

        if not change_set.has_changes():
            logger.info("No changes detected. Graph is up to date.")
            return change_set

        # 3. Process Changes (Phase 1 & 2)
        self._process_changes(change_set, current_files)

        return change_set

    def _process_changes(self, change_set: ChangeSet, current_files: dict):
        """
        Process the detected changes in two phases.
        """
        files_to_process = change_set.new_files + change_set.modified_files

        collection_results = []

        # Phase 1: Collection (Structure)
        logger.info("Starting Phase 1: Collection")
        for file_path in files_to_process:
            checksum = current_files.get(file_path)
            if checksum:
                logger.info(f"Collecting structure for: {file_path}")
                result = self.collector.process_file(file_path, checksum)
                if result:
                    collection_results.append(result)

        # Phase 2: Analysis (Bodies)
        logger.info("Starting Phase 2: Analysis")
        for result in collection_results:
            logger.info(
                "Analyzing changes for: %s",
                result.file_scope.file_path,
            )

            # 1. Delete Removed Scopes
            for scope_id in result.removed_scope_ids:
                logger.info(f"Deleting removed scope ID: {scope_id}")
                self.scope_manager.delete_scope(scope_id)

            # 2. Process File Body (Full Analysis)
            # We process the entire file AST every time it changes
            logger.info("Processing file body: %s", result.file_scope.qname)

            # Clear file-scope calls; children clear during traversal
            self.scope_manager.clear_calls(result.file_scope.id)

            # Parse the full AST tree
            # BodyParser traverses descendants and clears their calls en route
            self.body_parser.process_ast(result.file_scope)

        # Process Deleted files (Full file deletion)
        for file_path in change_set.deleted_files:
            logger.info(f"Processing file deletion: {file_path}")
            self.scope_manager.delete_file_scope(file_path)
