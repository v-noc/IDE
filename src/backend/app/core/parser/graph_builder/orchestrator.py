import logging
from typing import Optional
from pathlib import Path

from arango.database import StandardDatabase

from app.core.model.nodes import ProjectNode
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel
from app.core.parser.graph_builder.discovery.scanner import FileScanner, ScanResult
from app.core.parser.graph_builder.discovery.change_detector import (
    ChangeDetector,
    ChangeSet,
)

from app.core.parser.graph_builder.collection.collector import Collector
from app.core.parser.graph_builder.collection.hierarchy import FolderChange
from app.core.parser.graph_builder.analysis.body_parser import BodyParser
from app.core.parser.graph_builder.sync.graph_sync import MainGraphSyncService


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
        self.project_root = Path(self.project_path)
        # Main ArangoDB connection (optional for now)
        self.db = db

        # Initialize ScopeManager
        # Note: ScopeManager handles DB connection internally
        self.scope_manager = scope_manager or ScopeManager(project_node.name)

        # Initialize Jedi Adapter
        from app.core.parser.jedi_adapter.manager import JediProjectManager

        self.jedi_manager = JediProjectManager(self.project_root)

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

        # Initialize Sync components
        self.sync_service = MainGraphSyncService(self.db, self.project_node)
        self._pending_folder_changes: list[FolderChange] = []

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
        scan_result = self.file_scanner.scan()
        logger.info(
            "Scanned %d files across %d folders on disk",
            len(scan_result.files),
            len(scan_result.folders),
        )

        # 2. Detect Changes
        change_set = self.change_detector.detect_changes(scan_result)
        logger.info(f"Detected changes: {change_set}")

        if not change_set.has_changes() and not change_set.has_folder_changes():
            logger.info("No changes detected. Graph is up to date.")
            return change_set

        # 3. Process Changes (Phase 1 & 2)
        self._process_changes(change_set, scan_result)

        return change_set

    def _process_changes(self, change_set: ChangeSet, scan_result: ScanResult):
        """
        Process the detected changes in two phases.
        """
        self.collector.reset_session()
        files_to_process = change_set.new_files + change_set.modified_files

        collection_results = []
        folder_changes = []
        touched_folder_ids = set()

        # Handle folder additions proactively to ensure hierarchy exists
        for folder_path in change_set.new_folders:
            folder_result = self.collector.process_folder(folder_path)
            if folder_result:
                folder_changes.extend(folder_result)
                touched_folder_ids.update(fc.scope.id for fc in folder_result)

        # Phase 1: Collection (Structure)
        logger.info("Starting Phase 1: Collection")
        for file_path in files_to_process:
            checksum = scan_result.files.get(file_path)
            if checksum:
                logger.info(f"Collecting structure for: {file_path}")
                result = self.collector.process_file(file_path, checksum)
                if result:
                    collection_results.append(result)
                    folder_changes.extend(result.folder_changes)
                    touched_folder_ids.update(
                        fc.scope.id for fc in result.folder_changes)

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

        # Process Deleted folders before files to avoid orphan references
        for folder_path in change_set.deleted_folders:
            logger.info(f"Processing folder deletion: {folder_path}")
            self._handle_folder_deletion(
                folder_path, folder_changes, touched_folder_ids)

        # Process Deleted files (Full file deletion)
        for file_path in change_set.deleted_files:
            logger.info(f"Processing file deletion: {file_path}")
            self._handle_file_deletion(
                file_path, folder_changes, touched_folder_ids)

        for result in collection_results:
            self.sync_service.sync_file(result)

        logger.info("Folder changes prepared for sync: %d",
                    len(folder_changes))
        self._pending_folder_changes = folder_changes

    def _handle_folder_deletion(
        self,
        folder_path: str,
        folder_changes: list,
        touched_folder_ids: set,
    ) -> None:
        folder_scope = self._scope_from_path(folder_path, is_file=False)
        if not folder_scope:
            logger.warning(
                "Folder scope not found for deletion path: %s", folder_path)
            return

        self._append_folder_change(
            folder_changes, touched_folder_ids, folder_scope, "deleted"
        )
        self.scope_manager.delete_scope(folder_scope.id)

    def _handle_file_deletion(
        self,
        file_path: str,
        folder_changes: list,
        touched_folder_ids: set,
    ) -> None:

        self.scope_manager.delete_file_scope(file_path)
        self._touch_parent_folders(
            file_path, folder_changes, touched_folder_ids)

    def _touch_parent_folders(
        self,
        target_path: str,
        folder_changes: list,
        touched_folder_ids: set,
    ) -> None:
        try:
            rel_path = Path(target_path).relative_to(self.project_root)
        except ValueError:
            logger.warning("Path %s is outside project root %s",
                           target_path, self.project_root)
            return

        folder_parts = rel_path.parts[:-1]
        if not folder_parts:
            return

        current_qname = self.project_node.name

        for part in folder_parts:
            current_qname = f"{current_qname}.{part}"
            folder_scope = self.scope_manager.get_scope_by_qname(current_qname)
            if not folder_scope or folder_scope.id in touched_folder_ids:
                continue
            self._append_folder_change(
                folder_changes, touched_folder_ids, folder_scope, "updated"
            )

    def _append_folder_change(
        self,
        folder_changes: list,
        touched_folder_ids: set,
        scope: Optional[ScopeModel],
        action: str,
    ) -> None:
        if not scope or scope.id in touched_folder_ids:
            return
        folder_changes.append(FolderChange(scope=scope, action=action))
        touched_folder_ids.add(scope.id)

    def _scope_from_path(self, abs_path: str, is_file: bool) -> Optional[ScopeModel]:
        """
        Resolve a scope using a filesystem path by mapping to its qname.
        """
        try:
            rel_path = Path(abs_path).relative_to(self.project_root)
        except ValueError:
            logger.warning(
                "Path %s is outside project root %s", abs_path, self.project_root
            )
            return None

        parts = list(rel_path.parts)
        if not parts:
            return self.scope_manager.get_scope_by_qname(self.project_node.name)

        if is_file and parts:
            parts[-1] = Path(parts[-1]).stem

        qname = ".".join([self.project_node.name] + parts)
        return self.scope_manager.get_scope_by_qname(qname)
