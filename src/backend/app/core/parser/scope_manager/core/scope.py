from __future__ import annotations
import uuid
from enum import Enum
from typing import Optional, Dict, TYPE_CHECKING, Any, List

from pydantic import BaseModel, Field


if TYPE_CHECKING:
    from .symbol import Symbol


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
    OBJECT = "object"           # Object instance attributes (obj.attr = value)
    EXECUTION = "execution"     # Temporary scope for a single function call


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
    parent: Optional["Scope"] = Field(default=None, exclude=True)
    children: Dict[str, "Scope"] = Field(default_factory=dict)

    # --- Symbol Table ---
    symbols: Dict[str, Any] = Field(default_factory=dict)

    # --- Wildcard imports (from x import *) ---
    # Keep an ordered list of module scopes whose public names are visible in
    # this scope. The order is important to resolve duplicates correctly
    # (last import wins).
    wildcard_import_scopes: List["Scope"] = Field(
        default_factory=list,
        exclude=True
    )

    # code_position: CodePosition

    class Config:
        arbitrary_types_allowed = True

    def add_symbol(self, symbol: "Symbol"):
        """Registers a symbol defined directly in this scope."""
        if symbol.defining_scope != self:
            raise ValueError("Symbol's defining_scope must be this scope.")
        self.symbols[symbol.name] = symbol

    def add_child_scope(self, scope: "Scope"):
        """Adds a nested scope as a child of this scope."""
        scope.parent = self
        self.children[scope.name] = scope

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
        self.qname_cache = '.'.join(reversed(parts))
        return self.qname_cache

    def __repr__(self):
        return f"<Scope(name='{self.qualified_name}', type='{self.scope_type.value}')>"

    def add_wildcard_import(self, module_scope: "Scope"):
        """Register a module scope as a wildcard import source for this scope.
        Maintains insertion order and avoids duplicates while preserving
        last-import-wins semantics.
        """
        # Remove existing occurrence to re-append at the end (so last added
        # takes precedence).
        try:
            self.wildcard_import_scopes.remove(module_scope)
        except ValueError:
            pass
        self.wildcard_import_scopes.append(module_scope)
