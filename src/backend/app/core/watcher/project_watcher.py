from __future__ import annotations

import logging
from pathlib import Path
from threading import Timer
from typing import Callable, Optional

from watchdog.events import (
    FileSystemEventHandler,
    FileModifiedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
)
from watchdog.observers import Observer
from watchdog.observers.api import ObservedWatch

logger = logging.getLogger(__name__)


class ChangeHandler(FileSystemEventHandler):
    """Handles file system events."""

    def __init__(self, callback: Callable[[], None], debounce_seconds: float = 0.5):
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.timer: Optional[Timer] = None

    def _trigger(self):
        self.callback()

    def on_modified(self, event: FileModifiedEvent):
        if event.is_directory or not event.src_path.endswith(".py"):
            return
        logger.info(f"File modified: {event.src_path}")
        if self.timer:
            self.timer.cancel()
        self.timer = Timer(self.debounce_seconds, self._trigger)
        self.timer.start()

    def on_created(self, event: FileCreatedEvent):
        if event.is_directory or not event.src_path.endswith(".py"):
            return
        logger.info(f"File created: {event.src_path}")
        if self.timer:
            self.timer.cancel()
        self.timer = Timer(self.debounce_seconds, self._trigger)
        self.timer.start()

    def on_deleted(self, event: FileDeletedEvent):
        if event.is_directory or not event.src_path.endswith(".py"):
            return
        logger.info(f"File deleted: {event.src_path}")
        if self.timer:
            self.timer.cancel()
        self.timer = Timer(self.debounce_seconds, self._trigger)
        self.timer.start()


class ProjectWatcher:
    """Watches a project directory for changes."""

    def __init__(self, project_path: str, resync_callback: Callable[[], None]):
        self.project_path = Path(project_path)
        self.resync_callback = resync_callback
        self.observer = Observer()
        self.event_handler = ChangeHandler(self.resync_callback)
        self._watch: Optional[ObservedWatch] = None

    def start(self):
        """Starts the observer thread."""
        if not self.project_path.is_dir():
            logger.error(f"Path is not a directory: {self.project_path}")
            return

        if not self.observer.is_alive():
            self.observer = Observer()
            self.observer.start()
            logger.info(f"Observer thread started for {self.project_path}")

        # Schedule the watch
        self.resume()

    def stop(self):
        """Stops the observer completely."""
        if self.observer.is_alive():
            # First unschedule to stop receiving events
            if self._watch:
                try:
                    self.observer.unschedule(self._watch)
                    self._watch = None
                except Exception:
                    pass

            # Stop the observer
            self.observer.stop()

            # Don't join from within the callback thread to avoid "cannot join current thread" error
            # The observer will finish on its own
            try:
                import threading
                current_thread = threading.current_thread()
                # Only try to join if we're not in the observer thread itself
                # The observer thread has a name like "Thread-*" or "Observer-*"
                if current_thread is not self.observer and not current_thread.name.startswith("Observer"):
                    self.observer.join(timeout=1.0)
            except (RuntimeError, AttributeError):
                # If we can't join (e.g., from callback thread), just stop without joining
                # The observer will clean up on its own
                pass
            logger.info(f"Stopped observer for {self.project_path}")

    def pause(self):
        """
        Pauses watching by unscheduling the watch.
        This ensures NO events are processed or queued during this time.
        """
        if self.observer.is_alive() and self._watch:
            try:
                self.observer.unschedule(self._watch)
                self._watch = None
                logger.info(
                    f"Paused watching (unscheduled) {self.project_path}")
            except Exception as e:
                logger.error(f"Error pausing watcher: {e}")

    def resume(self):
        """
        Resumes watching by scheduling the watch again.
        Only new events from this point on will be caught.
        """
        if self.observer.is_alive() and self._watch is None:
            try:
                self._watch = self.observer.schedule(
                    self.event_handler,
                    str(self.project_path),
                    recursive=True
                )
                logger.info(f"Resumed watching {self.project_path}")
            except Exception as e:
                logger.error(f"Error resuming watcher: {e}")

    def is_running(self) -> bool:
        return self.observer.is_alive()

    def is_paused(self) -> bool:
        # If we have no active watch object, we are effectively paused
        return self._watch is None
