from concurrent.futures import ThreadPoolExecutor
import logging
import threading
import jedi
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class JediProjectManager:
    """
    Singleton-like manager for the Jedi Project.
    Ensures we have a consistent project context for analysis.
    """
    _instance = None

    def __init__(self, project_path: Path):
        self.project_path = project_path
        # Disable dynamic resolution features as they can be unstable/slow
        jedi.settings.dynamic_params_for_other_modules = False

        self.project = jedi.Project(path=str(project_path))
        logger.info(f"Initialized Jedi Project at: {project_path}")
        self.project = jedi.Project(path=str(project_path))
        # Single-threaded executor forces sequential access
        self.executor = ThreadPoolExecutor(max_workers=1)
        # Thread lock for Jedi operations (Jedi is not thread-safe)
        # Using RLock to allow reentrant locking from same thread
        self._lock = threading.RLock()

    def get_script(self, path: str, source: str) -> jedi.Script:
        # Acquire lock for thread-safe Jedi operations
        # Using RLock allows reentrant access if called from resolve_call
        with self._lock:
            def _get():
                return jedi.Script(code=source, path=path, project=self.project)
            return self.executor.submit(_get).result()

    def get_project(self) -> jedi.Project:
        return self.project
