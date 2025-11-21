# storage/scope_resolver.py
"""
Scope Resolution Service.
Implements LEGB (Local, Enclosing, Global, Builtin) name resolution.
Handles scope traversal and symbol lookup within scope hierarchies.
"""

from typing import List, Optional, Tuple
from ..storage.repository.repos import ScopeManagerRepository
from ..storage.models import ScopeModel, SymbolModel, ScopeType, SymbolType


class ScopeResolver:
    """Resolves names within scope hierarchies using LEGB rules."""

    def __init__(self, repo: ScopeManagerRepository):
        self.repo = repo

    def resolve_name(self, name: str, start_scope_id: str) -> Optional[SymbolModel]:
        """
        Resolve a name using LEGB rules (Local, Enclosing, Global, Builtin).

        Args:
            name: The name to resolve
            start_scope_id: The scope to start searching from

        Returns:
            The SymbolORM if found, None otherwise
        """
        # Walk up the scope chain
        scope_chain = self.repo.scopes.get_scope_chain(start_scope_id)

        for scope in scope_chain:
            symbol = self.repo.symbols.get_by_name_in_scope(name, scope.id)
            if symbol:
                return symbol

        # TODO: Check builtins if you have a builtin scope
        return None

    def resolve_name_with_chain(
        self, name: str, start_scope_id: str
    ) -> Tuple[Optional[SymbolModel], List[str]]:
        """
        Resolve a name and return the chain of scopes checked.
        Useful for debugging and understanding resolution.

        Args:
            name: The name to resolve
            start_scope_id: The scope to start searching from

        Returns:
            Tuple of (symbol, list of scope_ids checked)
        """
        scope_chain = self.repo.scopes.get_scope_chain(start_scope_id)
        scope_ids_checked = []

        for scope in scope_chain:
            scope_ids_checked.append(scope.id)
            symbol = self.repo.symbols.get_by_name_in_scope(name, scope.id)
            if symbol:
                return symbol, scope_ids_checked

        return None, scope_ids_checked

    def get_scope_hierarchy(self, scope_id: str) -> List[ScopeModel]:
        """
        Get the full hierarchy from root to scope.

        Args:
            scope_id: The scope to get hierarchy for

        Returns:
            List of scopes from root to target scope
        """
        chain = self.repo.scopes.get_scope_chain(scope_id)
        return list(reversed(chain))

    def is_accessible_from(self, symbol_scope_id: str, access_scope_id: str) -> bool:
        """
        Check if a symbol defined in symbol_scope_id is accessible from access_scope_id.
        In Python, nested scopes have access to parent scopes.

        Args:
            symbol_scope_id: The scope where the symbol is defined
            access_scope_id: The scope from which we're accessing

        Returns:
            True if accessible, False otherwise
        """
        # Check if symbol_scope_id is an ancestor of access_scope_id
        chain = self.repo.scopes.get_scope_chain(access_scope_id)
        scope_ids_in_chain = [s.id for s in chain]
        return symbol_scope_id in scope_ids_in_chain

    def find_all_scopes_by_type(self, scope_type: ScopeType) -> List[ScopeModel]:
        """Find all scopes of a specific type."""
        return self.repo.scopes.get_by_type(scope_type.value)

    def get_local_symbols(self, scope_id: str) -> List[SymbolModel]:
        """
        Get all symbols directly defined in a scope (not inherited).

        Args:
            scope_id: The scope to query

        Returns:
            List of symbols in that scope
        """
        return self.repo.symbols.get_in_scope(scope_id)

    def get_exported_symbols(self, scope_id: str) -> List[SymbolModel]:
        """
        Get symbols exported from a scope.
        In Python, typically all non-underscore names.

        Args:
            scope_id: The scope to query

        Returns:
            List of exported symbols
        """
        symbols = self.repo.symbols.get_in_scope(scope_id)
        return [s for s in symbols if not s.name.startswith("_")]

    def get_scope_by_name_in_scope(
        self, name: str, start_scope_id: str
    ) -> Optional[ScopeModel]:
        """
        Find a scope by name, searching up the hierarchy.
        Useful for class and function lookups.

        Args:
            name: The name of the scope
            start_scope_id: The scope to start searching from

        Returns:
            The ScopeModel if found, None otherwise
        """
        scope_chain = self.repo.scopes.get_scope_chain(start_scope_id)

        for scope in scope_chain:
            # Check children of this scope
            children = self.repo.scopes.get_children(scope.id)
            for child in children:
                if child.name == name:
                    return child

        return None

    def get_source_unit_scope(self, source_path: str) -> Optional[ScopeModel]:
        """
        Get the module-level scope for a source file.

        Args:
            source_path: The path to the source file

        Returns:
            The module scope, or None if not found
        """
        source_unit = self.repo.sources.get_by_path(source_path)
        if source_unit:
            return source_unit.scope
        return None

    def get_source_scope(self, source_id: str) -> Optional[ScopeModel]:
        """
        Get the module-level scope for a source file.

        Args:
            source_id: The source file ID

        Returns:
            The module scope, or None if not found
        """
        source_unit = self.repo.sources.get_by_id(source_id)
        if source_unit:
            return source_unit.scope
        return None

    def is_nested_in(self, inner_scope_id: str, outer_scope_id: str) -> bool:
        """
        Check if inner_scope is nested inside outer_scope.

        Args:
            inner_scope_id: The potentially nested scope
            outer_scope_id: The potentially outer scope

        Returns:
            True if inner is nested in outer, False otherwise
        """
        chain = self.repo.scopes.get_scope_chain(inner_scope_id)
        scope_ids = [s.id for s in chain]
        return outer_scope_id in scope_ids
