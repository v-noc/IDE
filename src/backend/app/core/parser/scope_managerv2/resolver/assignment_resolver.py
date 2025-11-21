# storage/assignment_resolver.py
"""
Assignment Resolution Service.
Handles variable assignments, reassignments, and value tracking.
Resolves assignment chains and tracks symbol origins.
"""

from typing import List, Optional, Dict, Tuple
from datetime import datetime
from ..storage.repository.repos import ScopeManagerRepository
from ..storage.models import SymbolModel, SymbolType
from .scope_resolver import ScopeResolver
from .symbol_resolver import SymbolResolver


class AssignmentResolver:
    """Resolves and tracks assignments."""

    def __init__(
        self,
        repo: ScopeManagerRepository,
        scope_resolver: ScopeResolver,
        symbol_resolver: SymbolResolver,
    ):
        self.repo = repo
        self.scope_resolver = scope_resolver
        self.symbol_resolver = symbol_resolver

    def resolve_assignment(self, symbol_id: str) -> Optional[SymbolModel]:
        """
        Resolve what a symbol is assigned to.
        Follows alias chains to find the original value.

        Args:
            symbol_id: The symbol to resolve

        Returns:
            The original symbol, or None if assignment is broken
        """
        return self.symbol_resolver.resolve_alias_chain(symbol_id)

    def get_assignment_chain(self, symbol_id: str) -> List[SymbolModel]:
        """
        Get the full chain of assignments for a symbol.
        Example: x = y; y = z returns [x, y, z]

        Args:
            symbol_id: The symbol to start with

        Returns:
            List of symbols in the assignment chain
        """
        chain = []
        visited = set()
        current_id = symbol_id

        while current_id:
            if current_id in visited:
                # Circular reference
                break
            visited.add(current_id)

            symbol = self.repo.symbols.get_by_id(current_id)
            if not symbol:
                break

            chain.append(symbol)

            if not symbol.assigned_to_id:
                break

            current_id = symbol.assigned_to_id

        return chain

    def is_assigned(self, symbol_id: str) -> bool:
        """
        Check if a symbol has an assignment.

        Args:
            symbol_id: The symbol to check

        Returns:
            True if assigned, False otherwise
        """
        symbol = self.repo.symbols.get_by_id(symbol_id)
        return symbol is not None and symbol.assigned_to_id is not None
