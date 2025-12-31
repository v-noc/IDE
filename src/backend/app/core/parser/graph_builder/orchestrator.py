
import logging
from pathlib import Path
from typing import Optional
import asyncio
from arangoasync.database import AsyncDatabase

from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.collection.collector import Collector
from app.core.parser.graph_builder.discovery.change_detector import (
    ChangeDetector,
    ChangeSet,
)
from app.core.parser.graph_builder.discovery.scanner import (
    FileScanner,
    ScanResult,
)
from app.core.parser.graph_builder.utils import (
    PhaseProcessor,
)
from app.core.parser.graph_builder.performance import tracker
from app.core.repository import Repositories

logger = logging.getLogger(__name__)


class GraphBuilderOrchestrator:
    """
    Orchestrator for coordinating graph building phases.

    Coordinates the overall graph building process:
    1. Discovery: Scan files and detect changes
    2. Collection: Build scope hierarchy
    3. Analysis: Parse AST and build call chains
    4. Sync: Synchronize to graph database (ArangoDB Direct)
    """

    def __init__(
        self,
        project_node: ProjectNode,
        db: Optional[AsyncDatabase] = None,
        # scope_manager: Optional[ScopeManager] = None, # Removed
        ignore_file_name: str = ".gitignore",
        max_concurrent_files: int = 50,
        max_concurrent_db: int = 100,
        batch_size: int = 100,
    ):
        self.project_node = project_node
        self.project_path = project_node.path
        self.project_root = Path(self.project_path)
        self.db = db
        self.max_concurrent_files = max_concurrent_files
        self.batch_size = batch_size
        self._file_semaphore = asyncio.Semaphore(max_concurrent_files)

        # Initialize Repositories (Required)
        if not db:
            raise ValueError(
                "Database connection is required for GraphBuilderOrchestrator")

        self.repos = Repositories(db)

        # Initialize Jedi Adapter
        from app.core.parser.jedi_adapter.manager import JediProjectManager
        self.jedi_manager = JediProjectManager(self.project_root)

        # Initialize Discovery components
        self.file_scanner = FileScanner(
            self.project_path,
            ignore_file_name=ignore_file_name,
        )
        self.change_detector = ChangeDetector(self.repos)

        # Initialize Collection components
        self.collector = Collector(
            self.project_node,
            self.repos,
            self.jedi_manager,
        )

        # Initialize Phase Processor
        # PhaseProcessor also needs refactoring to remove ScopeManager
        # For now, we update initialization to match what we have or remove incompatible args
        self.phase_processor = PhaseProcessor(
            self.project_node,
            self.project_path,
            self.repos,  # Replaces scope_manager
            self.collector,
            self.jedi_manager,
            batch_size=self.batch_size,
            max_concurrent_db=max_concurrent_db,
            max_concurrent_files=self.max_concurrent_files,
        )

    async def resync(self) -> ChangeSet:
        """
        Perform an incremental resync of the project.
        1. Scan files
        2. Detect changes
        3. Phase 1: Structure Collection (Scopes)
        4. Phase 2: Body Analysis (Calls)
        """
        print(
            "Starting resync for project: %s",
            self.project_node.name,
        )

        tracker.reset()

        # Ensure project root exists once (create if new, otherwise reuse).
        await self.collector.ensure_project_root()
        self.project_node = self.collector.project_node
        self.phase_processor.project_node = self.project_node

        # 1. Scan Disk
        scan_result = self.file_scanner.scan()
        logger.info(
            "Scanned %d files across %d folders on disk",
            len(scan_result.files),
            len(scan_result.folders),
        )

        # 2. Detect Changes
        change_set = await self.change_detector.detect_changes(scan_result)
        logger.info(f"Detected changes: {change_set}")

        if (
            not change_set.has_changes()
            and not change_set.has_folder_changes()
        ):
            logger.info("No changes detected. Graph is up to date.")
            return change_set

        # 3. Process Changes (Phase 1 & 2)
        await self._process_changes(change_set, scan_result)

        return change_set

    async def _process_changes(
        self, change_set: ChangeSet, scan_result: ScanResult
    ):
        """
        Process the detected changes in multiple phases.

        Phase 1: Collection - Build scope hierarchy
        Phase 2: Analysis - Parse AST and build call chains
        """
        folder_changes = []

        # Reset per-run caches and perform ID-first structure synchronization
        # (folders + file shells).
        self.collector.reset_session()
        folder_result = await self.collector.sync_structure(
            change_set, scan_result, batch_size=self.batch_size
        )
        if folder_result:
            folder_changes.extend(folder_result)

        # Phase 1: Collection (Structure)
        logger.info("Starting Phase 1: Collection")
        collection_results = (
            await self.phase_processor.process_collection_phase(
                change_set, scan_result
            )
        )

        # Phase 2: Analysis (Body parsing and call chain building)
        logger.info("Starting Phase 2: Analysis")
        print("Starting Phase 2: Analysis", flush=True)
        try:
            # Phase 2 refactoring is deferred.
            # We pass None for call_sync_service as we removed SyncService.
            await self.phase_processor.process_analysis_phase(
                collection_results, None
            )
            logger.info("Phase 2: Analysis completed")
            print("Phase 2: Analysis completed", flush=True)

        finally:
            # Ensure cleanup happens even if there's an error
            logger.debug("Phase 2 cleanup complete")

        logger.info("All phases completed successfully")
        print("All phases completed successfully", flush=True)

        tracker.print_report()
