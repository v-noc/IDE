# storage/qname_resolver.py
"""
Qualified Name (QName) Resolution Service.
Handles resolution of dotted names like 'module.Class.method'.
Resolves import paths and fully qualified identifiers.
"""

from typing import List, Optional, Tuple
from ..storage.repository.repos import ScopeManagerRepository
from ..storage.models import SymbolModel, ScopeModel, SymbolType, ScopeType
from .scope_resolver import ScopeResolver
from .symbol_resolver import SymbolResolver


class QNameResolver:
    """Resolves qualified names (dotted paths)."""

    def __init__(
        self,
        repo: ScopeManagerRepository,
        scope_resolver: ScopeResolver,
        symbol_resolver: SymbolResolver,
    ):
        self.repo = repo
        self.scope_resolver = scope_resolver
        self.symbol_resolver = symbol_resolver

    def resolve_qname(self, qname: str) -> Optional[SymbolModel]:
        """
        Resolve a fully qualified name like 'module.Class.method'.

        Args:
            qname: The qualified name as a dotted string

        Returns:
            The SymbolModel if found, None otherwise
        """
        parts = qname.split(".")
        if not parts:
            return None

        # Start at global scope (module level)
        current_scope = None
        current_symbol = None

        for i, part in enumerate(parts):
            if i == 0:
                # First part: look for module or top-level symbol
                # Try to find in module scope

                current_scope = self.repo.scopes.get_root()
                # Subsequent parts: look in current scope
                if not current_scope:
                    return None

            else:
                # Subsequent parts: look in current scope
                if not current_scope:
                    return None

                # Look for a symbol or scope with this name
                symbol = self.repo.symbols.get_by_name_in_scope(
                    part, current_scope.id)

                if symbol:
                    current_symbol = symbol
                    # If this symbol defines a scope (class or function), move into it
                    if symbol.defines_scope_id:
                        current_scope = self.repo.scopes.get_by_id(
                            symbol.defines_scope_id)
                else:
                    # Maybe it's a scope (nested class/function)
                    children = self.repo.scopes.get_children(current_scope.id)
                    found_child = None
                    for child in children:
                        if child.name == part:
                            found_child = child
                            break

                    if found_child:
                        current_scope = found_child
                        # The scope's primary symbol
                        current_symbol = None
                        for sym in self.repo.symbols.get_in_scope(found_child.parent_id or found_child.id):
                            if sym.name == part and sym.defines_scope_id == found_child.id:
                                current_symbol = sym
                                break
                    else:
                        return None

        return current_symbol

    def resolve_qname_to_scope(self, qname: str) -> Optional[ScopeModel]:
        """
        Resolve a qualified name to a scope (for class/function lookups).

        Args:
            qname: The qualified name as a dotted string

        Returns:
            The ScopeORM if found, None otherwise
        """
        symbol = self.resolve_qname(qname)
        if symbol and symbol.defines_scope_id:
            return self.repo.scopes.get_by_id(symbol.defines_scope_id)
        return None

    def resolve_relative_name(
        self, name: str, from_scope_id: str
    ) -> Optional[SymbolModel]:
        """
        Resolve a relative name (simple name, not dotted) from a given scope.

        Args:
            name: The name to resolve
            from_scope_id: The scope to resolve from

        Returns:
            The SymbolModel if found, None otherwise
        """
        return self.scope_resolver.resolve_name(name, from_scope_id)

    def get_qname_for_symbol(self, symbol_id: str) -> Optional[str]:
        """
        Get the qualified name for a symbol.

        Args:
            symbol_id: The symbol ID

        Returns:
            The qualified name as a dotted string, or None if not found
        """
        symbol = self.repo.symbols.get_by_id(symbol_id)
        if not symbol:
            return None

        scope = symbol.defining_scope

        if not scope:
            return symbol.name

        # Build path from scope hierarchy
        path_parts = [scope.name, symbol.name]
        current_scope = scope

        while current_scope.parent_id:
            current_scope = self.repo.scopes.get_by_id(current_scope.parent_id)
            if current_scope:
                path_parts.insert(0, current_scope.name)
            else:
                break

        return ".".join(path_parts)

    def get_qname_for_scope(self, scope_id: str) -> Optional[str]:
        """
        Get the qualified name for a scope.

        Args:
            scope_id: The scope ID

        Returns:
            The qualified name as a dotted string, or None if not found
        """
        scope = self.repo.scopes.get_by_id(scope_id)
        if not scope:
            return None

        path_parts = [scope.name]
        current_scope = scope

        while current_scope.parent_id:
            current_scope = self.repo.scopes.get_by_id(current_scope.parent_id)
            if current_scope:
                path_parts.insert(0, current_scope.name)
            else:
                break

        return ".".join(path_parts)

    def resolve_import_path(self, import_path: str) -> Tuple[Optional[str], List[str]]:
        """
        Resolve an import path like 'module.submodule.Class' to (module_id, [Class, ...]).

        Args:
            import_path: The import path to resolve

        Returns:
            Tuple of (source_id, remaining_path_parts) or (None, []) if not found
        """
        parts = import_path.split(".")

        # Try to match progressively longer prefixes to find the module
        for i in range(len(parts), 0, -1):
            potential_module = ".".join(parts[:i])
            sources = self.repo.sources.get_all()
            for source in sources:
                if self._matches_module_path(source, potential_module):
                    remaining = parts[i:]
                    return source.id, remaining

        return None, parts

    def _matches_module_path(self, source, module_path: str) -> bool:
        """Check if a source file matches a module path."""
        # Simple heuristic: convert file path to module path
        # e.g., /path/to/mymodule/submodule.py -> mymodule.submodule
        file_path = source.file_path
        module_from_path = file_path.replace("/", ".").replace(".py", "")
        return module_path in module_from_path

    def find_symbol_by_qname_partial(
        self, partial_qname: str, in_scope_id: Optional[str] = None
    ) -> List[SymbolModel]:
        """
        Find symbols matching a partial qualified name.
        Example: 'my_module.*' or 'MyClass.*'

        Args:
            partial_qname: The partial qualified name (may contain *)
            in_scope_id: Optional - limit search to a scope

        Returns:
            List of matching symbols
        """
        if "*" not in partial_qname:
            # Just resolve normally
            sym = self.resolve_qname(partial_qname)
            return [sym] if sym else []

        parts = partial_qname.split(".")
        base_qname = ".".join(p for p in parts if p != "*")

        # Resolve the base
        base_symbol = self.resolve_qname(base_qname) if base_qname else None
        base_scope = None

        if base_symbol and base_symbol.defines_scope_id:
            base_scope = self.repo.scopes.get_by_id(
                base_symbol.defines_scope_id)
        elif in_scope_id:
            base_scope = self.repo.scopes.get_by_id(in_scope_id)

        if not base_scope:
            return []

        # Return all symbols in base scope
        return self.repo.symbols.get_in_scope(base_scope.id)
