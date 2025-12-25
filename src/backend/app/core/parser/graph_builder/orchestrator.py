
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
    DeletionHandler,
    PathResolver,
    PhaseProcessor,
)
from app.core.parser.graph_builder.sync.graph_sync import (
    MainGraphSyncService,
)
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.repository import Repositories

logger = logging.getLogger(__name__)


class GraphBuilderOrchestrator:
    """
    Orchestrator for coordinating graph building phases.

    Coordinates the overall graph building process:
    1. Discovery: Scan files and detect changes
    2. Collection: Build scope hierarchy
    3. Analysis: Parse AST and build call chains
    4. Sync: Synchronize to graph database
    """

    def __init__(
        self,
        project_node: ProjectNode,
        db: Optional[AsyncDatabase] = None,
        scope_manager: Optional[ScopeManager] = None,
        ignore_file_name: str = ".gitignore",
        max_concurrent_files: int = 50,
        max_concurrent_db: int = 100,
        batch_size: int = 100,
    ):
        self.project_node = project_node
        self.project_path = project_node.path
        self._async_sync_service = None
        self.project_root = Path(self.project_path)
        self.db = db
        self.max_concurrent_files = max_concurrent_files
        self.batch_size = batch_size
        self._file_semaphore = asyncio.Semaphore(max_concurrent_files)

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

        # Initialize helper components
        self.path_resolver = PathResolver(
            self.project_node, self.scope_manager
        )
        self.deletion_handler = DeletionHandler(
            self.project_node, self.scope_manager, self.path_resolver
        )

        # Initialize Phase Processor
        self.phase_processor = PhaseProcessor(
            self.project_node,
            self.project_path,
            self.scope_manager,
            self.collector,
            self.jedi_manager,
            batch_size=self.batch_size,
            max_concurrent_db=max_concurrent_db,
            max_concurrent_files=self.max_concurrent_files,

        )

        # Initialize Sync components
        # Will create sync service with version when needed in _process_changes
        self.repos = Repositories(self.db) if self.db else None

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

        await self.scope_manager.initialize()

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
        self.scope_manager.close()

        return change_set

    async def _process_changes(
        self, change_set: ChangeSet, scan_result: ScanResult
    ):
        """
        Process the detected changes in multiple phases.

        Phase 1: Collection - Build scope hierarchy
        Phase 2: Analysis - Parse AST and build call chains
        Phase 3: Sync - Synchronize to graph database
        """
        folder_changes = []
        touched_folder_ids = set()

        # Reset per-run caches and perform ID-first structure synchronization
        # (folders + file shells).
        self.collector.reset_session()
        folder_result = await self.collector.sync_structure(
            change_set, scan_result, batch_size=self.batch_size
        )
        if folder_result:
            folder_changes.extend(folder_result)
            touched_folder_ids.update(fc.scope.id for fc in folder_result)

        # Phase 1: Collection (Structure)
        logger.info("Starting Phase 1: Collection")
        collection_results = (
            await self.phase_processor.process_collection_phase(
                change_set, scan_result
            )
        )

        # Collect folder changes from collection results
        for result in collection_results:
            folder_changes.extend(result.folder_changes)
            touched_folder_ids.update(
                fc.scope.id for fc in result.folder_changes
            )

        # Process Deleted files (Full file deletion)
        if change_set.deleted_files:
            await self.deletion_handler.handle_batch_file_deletions(
                [tp.path for tp in change_set.deleted_files if tp.path],
                folder_changes,
                touched_folder_ids,
            )

        # Phase 3: Sync scopes to graph database
        # Generate version at project level

        call_sync_service = None
        sync_service = None
        if self.repos:
            sync_service = MainGraphSyncService(
                self.repos,
                self.scope_manager,
                self.project_node,
            )

            await sync_service.sync_scope_hierarchy(
                self.project_node.id, change_set
            )
            call_sync_service = sync_service.call_sync
        else:
            logger.warning("No database connection for sync; skipping")

        # Phase 2: Analysis (Body parsing and call chain building)
        logger.info("Starting Phase 2: Analysis")
        print("Starting Phase 2: Analysis", flush=True)
        try:
            await self.phase_processor.process_analysis_phase(
                collection_results, call_sync_service
            )
            logger.info("Phase 2: Analysis completed")
            print("Phase 2: Analysis completed", flush=True)

        finally:
            # Ensure cleanup happens even if there's an error
            logger.debug("Phase 2 cleanup complete")

        if sync_service:
            logger.info("Syncing call chains to graph database...")
            print("Syncing call chains to graph database...", flush=True)
            try:
                await sync_service.call_sync.batch_sync_calls()
                logger.info("Call chain sync completed")
                print("Call chain sync completed", flush=True)
            except Exception as sync_exc:
                logger.error(
                    f"Error during batch sync: {sync_exc}", exc_info=True)
                print(f"Error during batch sync: {sync_exc}", flush=True)
                raise

        logger.info("All phases completed successfully")
        print("All phases completed successfully", flush=True)

        # Debugger: Visualize scope and call site graph
        # visualizer = GraphVisualizer(self.scope_manager)
        # visualizer.visualize_graph()

        # printer = CallSiteTreePrinter(self.scope_manager)
        # printer.print_call_site_tree()
