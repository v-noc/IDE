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
        jedi.settings.dynamic_params = False

        logger.info(f"Initialized Jedi Project at: {project_path}")

        self.project = jedi.Project(path=str(self.project_path.parent))
        self.env = jedi.InterpreterEnvironment()

    def get_script(self, path: str, source: str) -> jedi.Script:

        return jedi.Script(code=source, path=path, project=self.project, environment=self.env)

    def get_script(self, path: str) -> jedi.Script:
        return jedi.Script(path=path, project=self.project, environment=self.env)

    def get_project(self) -> jedi.Project:
        return self.project
