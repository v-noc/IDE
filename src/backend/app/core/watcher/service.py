from __future__ import annotations

import logging
import asyncio
from typing import Dict, Optional
from threading import Lock
from arangoasync.database import AsyncDatabase
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

    def __init__(self, db: AsyncDatabase | None = None):
        if not hasattr(self, 'initialized'):
            self.watchers: Dict[str, ProjectWatcher] = {}
            self.db = db
            self.socket_manager = get_socket_manager()
            self.main_event_loop: Optional[asyncio.AbstractEventLoop] = None
            self.initialized = True

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """Set the main event loop to use for async operations from sync threads."""
        self.main_event_loop = loop

    def set_db(self, db: AsyncDatabase):
        if self.db is None:
            self.db = db

    def start_watching(self, project_node: ProjectNode):
        project_id = project_node.id

        # Helper to run async socket events from the sync thread
        def emit_sync_event(event_type: str, message: str):
            try:
                # Try to use the main event loop if available
                if self.main_event_loop and self.main_event_loop.is_running():
                    # Schedule coroutine to run in the main event loop
                    future = asyncio.run_coroutine_threadsafe(
                        self.socket_manager.emit_to_project(
                            project_id,
                            event_type,
                            {"message": message, "projectId": project_id}
                        ),
                        self.main_event_loop
                    )
                    # Wait for the result (with timeout to avoid blocking forever)
                    future.result(timeout=5.0)
                else:
                    # Fallback: create a new event loop in this thread
                    # This works when called from a thread without an event loop
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # If loop is running, we can't use run_until_complete
                            # Create a task instead
                            asyncio.create_task(
                                self.socket_manager.emit_to_project(
                                    project_id,
                                    event_type,
                                    {"message": message, "projectId": project_id}
                                )
                            )
                        else:
                            loop.run_until_complete(
                                self.socket_manager.emit_to_project(
                                    project_id,
                                    event_type,
                                    {"message": message, "projectId": project_id}
                                )
                            )
                    except RuntimeError:
                        # No event loop in this thread, create a new one
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(
                                self.socket_manager.emit_to_project(
                                    project_id,
                                    event_type,
                                    {"message": message, "projectId": project_id}
                                )
                            )
                        finally:
                            loop.close()
            except Exception as e:
                logger.error(f"Socket emit failed: {e}", exc_info=True)

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
                # Use pause() which unschedules without joining threads
                self.pause_watching(project_id)

                from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator

                # Re-initialize orchestrator for the specific job
                # Note: We create a fresh one to ensure clean state
                orchestrator = GraphBuilderOrchestrator(
                    project_node=project_node,
                    db=self.db
                )

                # Perform the sync (orchestrator is async; we run it in the main loop)
                if self.main_event_loop and self.main_event_loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(
                        orchestrator.resync(),
                        self.main_event_loop,
                    )
                    changes = future.result(timeout=None)
                else:
                    # Fallback: run in a dedicated loop in this thread
                    changes = asyncio.run(orchestrator.resync())

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
        print(f"Started watching project {project_id}")

    def stop_watching(self, project_id: str):
        watcher = self.watchers.get(project_id)
        if watcher:
            watcher.stop()
            del self.watchers[project_id]

    def stop_all(self):
        for pid in list(self.watchers.keys()):
            self.stop_watching(pid)

    def pause_watching(self, project_id: str):
        """Pause watching by unscheduling the watch (non-blocking)."""
        watcher = self.watchers.get(project_id)
        if watcher:
            # Use pause() instead of stop() to avoid joining the thread from within callback
            watcher.pause()

    def resume_watching(self, project_id: str):
        watcher = self.watchers.get(project_id)
        if watcher:
            watcher.start()

# Dependency remains the same...


def get_watcher_service(request: Request, db: AsyncDatabase = Depends(get_db)) -> WatcherService:
    service = getattr(request.app.state, "watcher_service", None)
    if service is None:
        service = WatcherService()
        request.app.state.watcher_service = service
    service.set_db(db)
    return service
