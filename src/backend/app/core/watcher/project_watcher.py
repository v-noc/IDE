from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from watchdog.events import (
    FileSystemEventHandler,
    FileModifiedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
)
from watchdog.observers import Observer


logger = logging.getLogger(__name__)


class ChangeHandler(FileSystemEventHandler):
    """Handles file system events."""

    def __init__(self, project_path: Path, callback: Callable[[], None]):
        self.project_path = project_path
        self.callback = callback
        self.paused = False

    def on_modified(self, event: FileModifiedEvent):
        if self.paused:
            return
        if event.is_directory or not event.src_path.endswith(".py"):
            return
        logger.info(f"File modified: {event.src_path}")
        self.callback()

    def on_created(self, event: FileCreatedEvent):
        if self.paused:
            return
        if event.is_directory or not event.src_path.endswith(".py"):
            return
        logger.info(f"File created: {event.src_path}")
        self.callback()

    def on_deleted(self, event: FileDeletedEvent):
        if self.paused:
            return
        if event.is_directory or not event.src_path.endswith(".py"):
            return
        logger.info(f"File deleted: {event.src_path}")
        self.callback()

    def pause(self):
        """Pause the handler."""
        self.paused = True
        logger.info("Watcher is paused.")

    def resume(self):
        """Resume the handler."""
        self.paused = False
        logger.info("Watcher is resumed.")


class ProjectWatcher:
    """Watches a project directory for changes."""

    def __init__(self, project_path: str, resync_callback: Callable[[], None]):
        self.project_path = Path(project_path)
        self.resync_callback = resync_callback
        self.observer = Observer()
        self.event_handler = ChangeHandler(
            self.project_path, self.resync_callback)
        self._started = False

    def start(self):
        """Starts watching the project directory."""
        if not self.project_path.is_dir():
            logger.error(f"Path is not a directory: {self.project_path}")
            return

        # Recreate observer if it has been stopped previously
        if not self.observer.is_alive():
            self.observer = Observer()
            self.observer.schedule(self.event_handler, str(
                self.project_path), recursive=True)
            self.observer.start()
            self._started = True
            logger.info(f"Started watching {self.project_path}")
        else:
            logger.info(f"Observer already running for {self.project_path}")

    def stop(self):
        """Stops watching the project directory."""
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logger.info(f"Stopped watching {self.project_path}")
        self._started = False

    def pause(self):
        """Pause watching."""
        self.event_handler.pause()

    def resume(self):
        """Resume watching."""
        self.event_handler.resume()

    def is_running(self) -> bool:
        """Return True if the underlying observer thread is running."""
        return self.observer.is_alive()

    def is_paused(self) -> bool:
        """Return True if the handler is currently paused."""
        return getattr(self.event_handler, "paused", False)
