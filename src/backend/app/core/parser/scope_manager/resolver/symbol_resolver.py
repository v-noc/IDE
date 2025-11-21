# storage/symbol_resolver.py
"""
Symbol Resolution Service.
Handles symbol lookup, aliases, and references.
Resolves symbols through assignment chains and imports.
"""

from typing import List, Optional, Dict
from ..storage.repository.repos import ScopeManagerRepository
from ..storage.models import SymbolModel, SymbolType
from .scope_resolver import ScopeResolver


class SymbolResolver:
    """Resolves symbols and follows references."""

    def __init__(self, repo: ScopeManagerRepository, scope_resolver: ScopeResolver):
        self.repo = repo
        self.scope_resolver = scope_resolver

    def get_symbol_definition(self, symbol_id: str, include_stale: bool = True) -> Optional[SymbolModel]:
        """
        Get the definition of a symbol.

        Args:
            symbol_id: The symbol ID
            include_stale: Whether to include stale symbols

        Returns:
            The SymbolModel, or None if not found
        """
        return self.repo.symbols.get_by_id(symbol_id, include_stale=include_stale)

    def resolve_alias_chain(self, symbol_id: str, include_stale: bool = True) -> Optional[SymbolModel]:
        """
        Follow an alias chain to find the original symbol.
        Example: x = y; y = z; resolve_alias_chain(x) -> z

        Args:
            symbol_id: The symbol to start with
            include_stale: Whether to traverse/return stale symbols

        Returns:
            The final symbol in the chain, or None if chain is broken
        """
        visited = set()
        current_id = symbol_id

        while current_id:
            if current_id in visited:
                # Circular reference
                return None
            visited.add(current_id)

            symbol = self.repo.symbols.get_by_id(
                current_id, include_stale=include_stale)
            if not symbol:
                return None

            # Check if this symbol is stale (if we care)
            if not include_stale and symbol.is_stale:
                return None

            # If not an alias, this is the definition
            if not symbol.assigned_to_id:
                return symbol

            # Check if the target exists and is valid
            target_id = symbol.assigned_to_id

            if not include_stale:
                target = self.repo.symbols.get_by_id(
                    target_id, include_stale=False)
                if not target:
                    # Target is missing or stale, so the chain is broken
                    return None

            current_id = target_id

        return None

    def get_all_aliases(self, symbol_id: str) -> List[SymbolModel]:
        """
        Get all symbols that alias to this symbol.
        Example: if x = original_func, get_all_aliases(original_func) includes x

        Args:
            symbol_id: The symbol to find aliases for

        Returns:
            List of symbols that alias to this symbol
        """
        return self.repo.symbols.get_by_assigned_to(symbol_id)

    def find_all_references(self, symbol_id: str) -> List[SymbolModel]:
        """
        Find all direct references to a symbol (symbols assigned to it).
        This is shallow - only direct assignments, not transitive.

        Args:
            symbol_id: The symbol to find references for

        Returns:
            List of symbols that reference this one
        """
        return self.repo.symbols.get_by_assigned_to(symbol_id)

    def get_symbol_type(self, symbol_id: str) -> Optional[SymbolType]:
        """
        Get the type of a symbol.

        Args:
            symbol_id: The symbol ID

        Returns:
            The SymbolType, or None if not found
        """
        symbol = self.repo.symbols.get_by_id(symbol_id)
        if symbol:
            return SymbolType(symbol.symbol_type)
        return None

    def find_symbols_by_name(
        self, name: str, source_id: Optional[str] = None
    ) -> List[SymbolModel]:
        """
        Find all symbols with a given name (can be in multiple scopes).

        Args:
            name: The symbol name to find
            source_id: Optional - limit search to a specific source file

        Returns:
            List of symbols with that name
        """
        if source_id:
            symbols = self.repo.symbols.get_by_source(source_id)
        else:
            symbols = self.repo.symbols.get_by_type(SymbolType.VARIABLE.value)
            # Get all symbols across all sources
            all_types = [t.value for t in SymbolType]
            symbols = []
            for symbol_type in all_types:
                symbols.extend(self.repo.symbols.get_by_type(symbol_type))

        return [s for s in symbols if s.name == name]

    def get_instance_scope(self, symbol_id: str) -> Optional:
        """
        Get the instance scope for an object symbol.
        Example: if x = MyClass(), get_instance_scope(x) returns the instance scope

        Args:
            symbol_id: The symbol ID

        Returns:
            The instance scope, or None if not an instance
        """
        symbol = self.repo.symbols.get_by_id(symbol_id)
        if symbol and symbol.instance_scope_id:
            return self.repo.scopes.get_by_id(symbol.instance_scope_id)
        return None

    def get_defining_scope(self, symbol_id: str) -> Optional:
        """
        Get the scope where a symbol is defined.

        Args:
            symbol_id: The symbol ID

        Returns:
            The defining scope
        """
        symbol = self.repo.symbols.get_by_id(symbol_id)
        if symbol:
            return self.repo.scopes.get_by_id(symbol.defining_scope_id)
        return None

    def get_symbols_of_type(self, symbol_type: SymbolType) -> List[SymbolModel]:
        """
        Get all symbols of a specific type.

        Args:
            symbol_type: The SymbolType to filter by

        Returns:
            List of symbols of that type
        """
        return self.repo.symbols.get_by_type(symbol_type.value)

    def is_builtin(self, symbol_id: str) -> bool:
        """
        Check if a symbol is a builtin.

        Args:
            symbol_id: The symbol ID

        Returns:
            True if the symbol is a builtin, False otherwise
        """
        symbol = self.repo.symbols.get_by_id(symbol_id)
        if not symbol:
            return False
        # Builtins would typically have metadata marking them
        return symbol.attrs.get("is_builtin", False) if symbol.attrs else False

    def get_symbol_metadata(self, symbol_id: str) -> Dict:
        """
        Get metadata associated with a symbol.

        Args:
            symbol_id: The symbol ID

        Returns:
            Dictionary of metadata
        """
        symbol = self.repo.symbols.get_by_id(symbol_id)
        if symbol:
            return symbol.attrs or {}
        return {}

    def set_symbol_metadata(self, symbol_id: str, metadata: Dict):
        """
        Update metadata for a symbol.

        Args:
            symbol_id: The symbol ID
            metadata: The metadata to set
        """
        symbol = self.repo.symbols.get_by_id(symbol_id)
        if symbol:
            symbol.attrs = metadata
