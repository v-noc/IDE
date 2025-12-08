import logging
import time

from app.core.model.nodes import ProjectNode
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.repository import Repositories
from app.core.services.call_service import CallService
from app.core.parser.graph_builder.sync.sync_helpers import SyncHelpers
from app.core.parser.graph_builder.sync.scope_sync import ScopeSyncService
from app.core.parser.graph_builder.sync.call_sync import CallSyncService

logger = logging.getLogger(__name__)


class MainGraphSyncService:
    """
    Graph Sync Service for synchronizing scope hierarchy to graph database.

    Two-phase approach:
    - Phase 1: Create/update nodes with hierarchy, contains edges, version
    - Phase 2: Sync call chains
    - Version is generated at project level (in orchestrator)
    """

    def __init__(
        self,
        repos: Repositories,
        scope_manager: ScopeManager,
        project_node: ProjectNode,
        sync_version: int,
    ):
        self.repos = repos
        self.scope_manager = scope_manager
        self.project_node = project_node
        self.sync_version = sync_version

        # Initialize helpers
        self.helpers = SyncHelpers(repos, sync_version)

        # Initialize services
        self.call_service = CallService(repos)
        self.scope_sync = ScopeSyncService(scope_manager, self.helpers)
        self.call_sync = CallSyncService(
            scope_manager, self.call_service, self.helpers
        )

    def sync_scope_hierarchy(self, root_scope_id: str):
        """
        Phase 1: Sync scope hierarchy starting from root_scope_id.

        Traverses all child scopes and:
        - Creates/updates nodes (only version updated on existing nodes)
        - Establishes contain edges

        Args:
            root_scope_id: The scope ID to start traversal from
        """
        logger.info(
            f"Phase 1: Syncing scope hierarchy from {root_scope_id} "
            f"with version {self.sync_version}"
        )

        # Update project node version so version filtering works correctly
        if self.project_node:
            self.project_node.current_version = self.sync_version
            self.repos.project_repo.update(
                self.project_node.key, self.project_node
            )

        print("Scope hierarchy synced")
        time_start = time.time()
        self.scope_sync.sync_scope_hierarchy(
            root_scope_id, self.project_node.id
        )
        # self.sync_call_chains(root_scope_id)
        time_end = time.time()
        print(
            f"Time taken to sync call chains: {time_end - time_start} seconds")

    def sync_call_chains(self, root_scope_id: str):
        """
        Phase 2: Sync call chains AFTER scopes are fully synced and
        call sites have been registered in the scope manager.

        This creates/updates CallNode documents and ensures
        targets and contains edges with the version.

        Args:
            root_scope_id: The root scope ID to start from
        """
        logger.info(
            "Phase 2: Syncing call chains from %s with version %s",
            root_scope_id,
            self.sync_version,
        )

        self.call_sync.sync_call_chains(root_scope_id)
