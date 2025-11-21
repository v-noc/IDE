# storage/writers/assignment_writer.py
"""
Assignment Writer - Handle creation and management of assignments and links.
"""

from typing import Optional
from ..storage.repository.repos import ScopeManagerRepository


class AssignmentWriter:
    """Write operations for assignments."""

    def __init__(self, repo: ScopeManagerRepository):
        self.repo = repo

    def assign_symbol(self, symbol_id: str, assigned_to_id: str) -> bool:
        """
        Assign one symbol to another (create alias).
        Example: x = y

        Args:
            symbol_id: The symbol being assigned (x)
            assigned_to_id: The symbol it's assigned to (y)

        Returns:
            True if successful, False otherwise
        """
        symbol = self.repo.symbols.get_by_id(symbol_id)
        if symbol:
            symbol.assigned_to_id = assigned_to_id
            self.repo.symbols.update(symbol)

            return True
        return False

    def unassign_symbol(self, symbol_id: str) -> bool:
        """
        Remove assignment from a symbol.

        Args:
            symbol_id: The symbol ID

        Returns:
            True if successful, False otherwise
        """
        symbol = self.repo.symbols.get_by_id(symbol_id)
        if symbol:
            symbol.assigned_to_id = None
            self.repo.symbols.update(symbol)
            return True
        return False

    def reassign_symbol(self, symbol_id: str, new_assigned_to_id: str) -> bool:
        """
        Change what a symbol is assigned to.

        Args:
            symbol_id: The symbol ID
            new_assigned_to_id: New assignment target

        Returns:
            True if successful, False otherwise
        """
        return self.assign_symbol(symbol_id, new_assigned_to_id)

    def set_instance_scope(self, symbol_id: str, instance_scope_id: str) -> bool:
        """
        Set the instance scope for a symbol (for object instances).

        Args:
            symbol_id: The symbol ID
            instance_scope_id: The instance scope ID

        Returns:
            True if successful, False otherwise
        """
        symbol = self.repo.symbols.get_by_id(symbol_id)
        if symbol:
            symbol.instance_scope_id = instance_scope_id
            return True
        return False

    def set_defines_scope(self, symbol_id: str, scope_id: str) -> bool:
        """
        Link a symbol to a scope it defines (for classes/functions).

        Args:
            symbol_id: The symbol ID
            scope_id: The scope it defines

        Returns:
            True if successful, False otherwise
        """
        symbol = self.repo.symbols.get_by_id(symbol_id)
        if symbol:
            symbol.defines_scope_id = scope_id
            return True
        return False
