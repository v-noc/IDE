from __future__ import annotations

import logging
from typing import Dict

from arango.database import StandardDatabase
from fastapi import Depends


from app.core.model.nodes import ProjectNode
from app.core.watcher.project_watcher import ProjectWatcher
from threading import Lock

from app.db.client import get_db

logger = logging.getLogger(__name__)


class WatcherService:
    """Manages file watchers for projects."""

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
            self.initialized = True
            logger.info("WatcherService initialized.")

    def set_db(self, db: StandardDatabase):
        if self.db is None:
            self.db = db
            logger.info("Database connection set for WatcherService.")

    def start_watching(self, project_node: ProjectNode):
        """Starts watching a project if not already watched."""
        project_id = project_node.id
        if project_id in self.watchers:
            logger.info(f"Project {project_id} is already being watched.")
            return

        def resync_project():
            from app.core.parser.graph_builder import GraphBuilder
            logger.info(f"Resyncing project {project_node.name}...")
            try:
                if self.db is None:
                    logger.error("Database not set in WatcherService.")
                    return

                # Temporarily pause the watcher to avoid loops from file modifications
                self.pause_watching(project_id)

                graph_builder = GraphBuilder(
                    project_node.path, project_node, self.db)
                graph_builder.build(project_node.name,
                                    project_node.description)
                logger.info(
                    f"Project {project_node.name} resynced successfully.")

            except Exception as e:
                logger.error(
                    f"Error resyncing project {project_node.name}: {e}")
            finally:
                # Always resume the watcher
                self.resume_watching(project_id)

        watcher = ProjectWatcher(project_node.path, resync_project)
        watcher.start()
        self.watchers[project_id] = watcher
        logger.info(
            f"Started watching project {project_id} at {project_node.path}")

    def stop_watching(self, project_id: str):
        """Stops watching a project."""
        watcher = self.watchers.get(project_id)
        if watcher:
            watcher.stop()
            del self.watchers[project_id]
            logger.info(f"Stopped watching project {project_id}")

    def pause_watching(self, project_id: str):
        """Pause watching a project."""
        watcher = self.watchers.get(project_id)
        if watcher:
            watcher.pause()
            logger.info(f"Paused watching project {project_id}")

    def resume_watching(self, project_id: str):
        """Resume watching a project."""
        watcher = self.watchers.get(project_id)
        if watcher:
            watcher.resume()
            logger.info(f"Resumed watching project {project_id}")


def get_watcher_service(db: StandardDatabase = Depends(get_db)) -> WatcherService:
    """Factory for WatcherService."""
    service = WatcherService()
    service.set_db(db)
    return service
