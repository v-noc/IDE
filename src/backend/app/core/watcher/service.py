from __future__ import annotations

import logging
import asyncio
from typing import Dict
from threading import Lock
from arango.database import StandardDatabase
from fastapi import Depends, Request

from app.core.model.nodes import ProjectNode
from app.core.watcher.project_watcher import ProjectWatcher
from app.core.socket.manager import get_socket_manager
from app.db.client import get_db

logger = logging.getLogger(__name__)


class WatcherService:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db: StandardDatabase | None = None):
        if not hasattr(self, 'initialized'):
            self.watchers: Dict[str, ProjectWatcher] = {}
            self.db = db
            self.socket_manager = get_socket_manager()
            self.initialized = True

    def set_db(self, db: StandardDatabase):
        if self.db is None:
            self.db = db

    def start_watching(self, project_node: ProjectNode):
        project_id = project_node.id

        # Helper to run async socket events from the sync thread
        def emit_sync_event(event_type: str, message: str):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    self.socket_manager.emit_to_project(
                        project_id,
                        event_type,
                        {"message": message, "projectId": project_id}
                    )
                )
                loop.close()
            except Exception as e:
                logger.error(f"Socket emit failed: {e}")

        if project_id in self.watchers:
            watcher = self.watchers[project_id]
            if not watcher.is_running():
                watcher.start()
            elif watcher.is_paused():
                watcher.resume()
            return

        def resync_project():
            logger.info(f"Triggering resync for {project_node.name}")

            # 1. Notify Frontend: Sync Started
            emit_sync_event("sync_started", "Detecting changes...")

            try:
                if self.db is None:
                    return

                # 2. Hard Pause to prevent loops/duplicate events
                self.pause_watching(project_id)

                from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator

                # Re-initialize orchestrator for the specific job
                # Note: We create a fresh one to ensure clean state
                orchestrator = GraphBuilderOrchestrator(
                    project_node=project_node,
                    db=self.db
                )

                # Perform the sync
                changes = orchestrator.resync()

                # 3. Notify Frontend: Sync Complete
                msg = "Sync complete."
                if changes and (changes.has_changes() or changes.has_folder_changes()):
                    msg = f"Synced {len(changes.modified_files)} changes."

                emit_sync_event("sync_complete", msg)
                logger.info(f"Project {project_node.name} resynced.")

            except Exception as e:
                logger.error(f"Error resyncing {project_node.name}: {e}")
                emit_sync_event("sync_error", str(e))
            finally:
                # 4. Resume watching (only catch NEW events from now on)
                self.resume_watching(project_id)

        # Initialize and start
        watcher = ProjectWatcher(project_node.path, resync_project)
        watcher.start()
        self.watchers[project_id] = watcher
        logger.info(f"Started watching project {project_id}")

    def stop_watching(self, project_id: str):
        watcher = self.watchers.get(project_id)
        if watcher:
            watcher.stop()
            del self.watchers[project_id]

    def stop_all(self):
        for pid in list(self.watchers.keys()):
            self.stop_watching(pid)

    def pause_watching(self, project_id: str):
        watcher = self.watchers.get(project_id)
        if watcher:
            watcher.pause()

    def resume_watching(self, project_id: str):
        watcher = self.watchers.get(project_id)
        if watcher:
            watcher.resume()

# Dependency remains the same...


def get_watcher_service(request: Request, db: StandardDatabase = Depends(get_db)) -> WatcherService:
    service = getattr(request.app.state, "watcher_service", None)
    if service is None:
        service = WatcherService()
        request.app.state.watcher_service = service
    service.set_db(db)
    return service
