"""Path resolution utilities for converting filesystem paths to scopes."""
import logging
from pathlib import Path
from typing import Optional

from app.core.model.nodes import ProjectNode
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel

logger = logging.getLogger(__name__)


class PathResolver:
    """Resolves scopes from filesystem paths."""

    def __init__(self, project_node: ProjectNode, scope_manager: ScopeManager):
        self.project_node = project_node
        self.project_root = Path(project_node.path)
        self.scope_manager = scope_manager

    def scope_from_path(
        self, abs_path: str, is_file: bool
    ) -> Optional[ScopeModel]:
        """
        Resolve a scope using a filesystem path by mapping to its qname.

        Args:
            abs_path: Absolute filesystem path
            is_file: Whether the path refers to a file (True) or folder (False)

        Returns:
            ScopeModel if found, None otherwise
        """
        try:
            rel_path = Path(abs_path).relative_to(self.project_root)
        except ValueError:
            logger.warning(
                "Path %s is outside project root %s",
                abs_path,
                self.project_root,
            )
            return None

        parts = list(rel_path.parts)
        if not parts:
            return self.scope_manager.get_scope_by_qname(self.project_node.name)

        if is_file and parts:
            parts[-1] = Path(parts[-1]).stem

        qname = ".".join([self.project_node.name] + parts)
        return self.scope_manager.get_scope_by_qname(qname)
