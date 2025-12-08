import logging
from typing import List

from app.core.parser.scope_manager.manager import ScopeManager

logger = logging.getLogger(__name__)

class ResolutionService:
    def __init__(self, scope_manager: ScopeManager):
        self.manager = scope_manager

    def resolve_all(self):
        """
        Attempt to resolve all unresolved call sites in the graph.
        """
        # Placeholder for future logic
        pass

    def resolve_scope(self, scope_id: str):
        """
        Attempt to resolve calls within a specific scope.
        """
        pass
