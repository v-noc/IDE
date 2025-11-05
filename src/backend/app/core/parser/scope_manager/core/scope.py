from __future__ import annotations
import uuid
from enum import Enum
from typing import Optional, Dict, TYPE_CHECKING, List

from pydantic import BaseModel, Field


if TYPE_CHECKING:
    from .symbol import Symbol

    from app.core.parser.scope_manager.storage.symbol_table import SymbolTable


class ScopeType(str, Enum):
    """
    An enumeration of the basic types of scopes.
    """

    MODULE = "module"
    FUNCTION = "function"
    CLASS = "class"
    COMPREHENSION = "comprehension"
    PROJECT = "project"

    # --- Execution context types ---
    OBJECT = "object"  # Object instance attributes (obj.attr = value)
    EXECUTION = "execution"  # Temporary scope for a single function call


class Scope(BaseModel):
    """
    Represents a lexical scope, forming a node in the scope hierarchy tree.
    It holds symbols defined directly within it and links to
    parent/child scopes.
    """

    qname_cache: Optional[str] = Field(default=None, exclude=True)
    # --- Core Identification ---

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # e.g., "my_function", "MyClass", or "__main__"
    scope_type: ScopeType

    # --- Hierarchy Links ---
    parent_id: Optional[str] = Field(default=None)
    child_scope_ids: List[str] = Field(default_factory=list)

    # --- Symbol Table ---
    symbol_ids: List[str] = Field(default_factory=list)

    # --- Wildcard imports (from x import *) ---
    # Keep an ordered list of module scopes whose public names are visible in
    # this scope. The order is important to resolve duplicates correctly
    # (last import wins).
    wildcard_import_scope_ids: List[str] = Field(
        default_factory=list,
    )

    # code_position: CodePosition

    # --- Runtime Context (not stored) ---
    _table: Optional[SymbolTable] = None

    # --- Caches (for performance) ---
    _parent_cache: Optional[Scope] = None
    _symbols_cache: Optional[Dict[str, Symbol]] = None
    _children_cache: Optional[Dict[str, Scope]] = None

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = False

    def bind_table(self, table: SymbolTable) -> Scope:
        """Bind this scope to a SymbolTable for relationship navigation."""
        self._table = table
        return self

    @property
    def wildcard_import_scopes(self) -> List[Scope]:
        """Get the wildcard import scopes."""
        scopes = [
            self._table.get_scope(id)
            for id in self.wildcard_import_scope_ids
        ]
        new_scopes = []
        for scope in scopes:
            if scope:
                scope.bind_table(self._table)
                new_scopes.append(scope)
        return new_scopes

    @property
    def parent(self) -> Optional[Scope]:
        """
        Lazy-load the parent scope.
        This looks like object navigation but is actually a DB query.
        """
        if not self._table:
            raise RuntimeError(
                (
                    "Scope must be bound to a SymbolTable "
                    f"{self.qualified_name} to access relationships"
                )
            )

        if self._parent_cache is not None:
            return self._parent_cache

        if self.parent_id:
            self._parent_cache = self._table.get_scope(self.parent_id)
            if self._parent_cache:
                self._parent_cache.bind_table(self._table)

        return self._parent_cache

    @property
    def symbols(self) -> Dict[str, Symbol]:
        """
        Lazy-load all symbols in this scope.
        Uses an optimized batch query.
        """
        if not self._table:
            raise RuntimeError(
                f"Scope must be bound to a SymbolTable {self.qualified_name}"
            )

        if self._symbols_cache is not None:
            return self._symbols_cache

        # This is ONE database query, not N queries!
        self._symbols_cache = {
            symbol.name: symbol
            for symbol in self._table.get_symbols_by_scope(self.id)
        }

        # Bind each symbol to the table
        for symbol in self._symbols_cache.values():
            symbol.bind_table(self._table)

        return self._symbols_cache

    @property
    def children(self) -> Dict[str, Scope]:
        """Lazy-load all child scopes."""
        if not self._table:
            raise RuntimeError(
                f"Scope must be bound to a SymbolTable {self.qualified_name}"
            )

        if self._children_cache is not None:
            return self._children_cache

        self._children_cache = {
            scope.name: scope
            for scope in self._table.get_child_scopes(self.id)
        }

        for child in self._children_cache.values():
            child.bind_table(self._table)

        return self._children_cache

    def get_symbol(self, name: str) -> Optional[Symbol]:
        """Get a symbol by name from this scope."""
        if name in self.symbol_ids:
            if not self._table:
                raise RuntimeError(
                    f"Scope must be bound to a SymbolTable {self.qualified_name}"
                )
            symbol = self._table.get_symbol(self.symbol_ids[name])
            if symbol:
                symbol.bind_table(self._table)
            return symbol
        return None

    def add_symbol(self, symbol: "Symbol"):
        """Registers a symbol defined directly in this scope."""
        if symbol.defining_scope_id != self.id:
            raise ValueError("Symbol's defining_scope must be this scope.")
        self.symbols[symbol.name] = symbol
        self.symbol_ids.append(symbol.id)
        self._table.save_symbol(symbol)

    def add_child_scope(self, scope: "Scope"):
        """Adds a nested scope as a child of this scope."""
        scope.parent_id = self.id
        self.children[scope.name] = scope
        self.child_scope_ids.append(scope.id)

        self._table.save_scope(scope)
        self._table.save_scope(self)

    @property
    def qualified_name(self) -> str:
        """Computes the fully qualified name on the fly."""
        if self.qname_cache:
            return self.qname_cache
        parts = []
        current = self
        while current:
            parts.append(current.name)
            current = current.parent
        self.qname_cache = ".".join(reversed(parts))
        return self.qname_cache

    def __repr__(self):
        return (
            f"<Scope(name='{self.qualified_name}', "
            f"type='{self.scope_type.value}')>"
        )

    def add_wildcard_import(self, module_scope: "Scope"):
        """Register a module scope as a wildcard import source for this scope.
        Maintains insertion order and avoids duplicates while preserving
        last-import-wins semantics.
        """
        # Remove existing occurrence to re-append at the end (so last added
        # takes precedence).
        try:
            self.wildcard_import_scope_ids.remove(module_scope.id)
        except ValueError:
            pass
        self.wildcard_import_scope_ids.append(module_scope.id)
        self._table.save_scope(self)

    def remove_wildcard_import(self, module_scope: "Scope") -> None:
        """Unregister a module scope from wildcard imports for this scope."""
        try:
            self.wildcard_import_scope_ids.remove(module_scope.id)
        except ValueError:
            return
        self._table.save_scope(self)
