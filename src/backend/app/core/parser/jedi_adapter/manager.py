import logging
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
        self.project = jedi.Project(path=str(project_path))
        logger.info(f"Initialized Jedi Project at: {project_path}")

    def get_project(self) -> jedi.Project:
        return self.project

    def get_script(self, path: str, source: str) -> jedi.Script:
        """
        Create a Jedi Script for a file with the project context.
        """
        print(f"Getting script for: {path}")
        print(f"Project: {self.project}")
        return jedi.Script(code=source, path=path, project=self.project)
