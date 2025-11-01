from __future__ import annotations
from enum import Enum
from typing import TYPE_CHECKING, Optional, Dict, Any, Set
from pydantic import BaseModel, Field
å
if TYPE_CHECKING:
    from .scope import Scope


class SymbolType(str, Enum):
    """
    An enumeration of the basic types of symbols we can identify.
    This is kept simple and can be extended if more granularity is needed.
    """

    VARIABLE = "variable"
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    IMPORT = "import"
    PARAMETER = "parameter"
    PROJECT = "project"
    # -- Add ONLY essential dynamic types --
    # Instantiated object (obj = MyClass())
    OBJECT_INSTANCE = "object_instance"
    CAPTURED_CLOSURE = "captured_closure"  # Function with captured environment
    UNKNOWN = "unknown"


class Symbol(BaseModel):
    """
    Represents a single symbol's definition within a scope.
    It contains only the essential information about its declaration.
    """

    # --- Core Identification ---
    name: str  # The name of the symbol, e.g., "my_variable"
    symbol_type: SymbolType

    # --- Definitional Context ---
    # A reference to the scope object where this symbol is defined.
    # This avoids storing scope IDs and allows direct traversal.
    defining_scope: "Scope" = Field(..., exclude=True)

    # code_position: CodePosition

    # --- Assignment Tracking ---
    # Tracks what this symbol is assigned to (for alias resolution)
    assigned_to: Optional["Symbol"] = Field(default=None, exclude=True)

    # Tracks what symbols are assigned to this symbol (reverse mapping)
    assigned_from: Set["Symbol"] = Field(default_factory=set, exclude=True)

    # --- Flexible Metadata ---
    # A generic dictionary to hold extra information without cluttering the model.
    # This is where details like `is_async`, `decorators`, `base_classes`, etc., can be stored.
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # For closures: Link to the frame this function captured (kept as Any to avoid early import cycles)
    captured_frame: Optional[Any] = Field(
        default=None, exclude=True, description="Frame this closure captured"
    )

    instance_scope: Optional["Scope"] = Field(
        default=None, exclude=True, description="Scope for object instance attributes"
    )

    class Config:
        arbitrary_types_allowed = True

    def __hash__(self):
        # Unique identifier for a symbol is its name and the scope it's defined in.
        return hash((self.name, id(self.defining_scope)))

    def is_instance(self) -> bool:
        """Check if this symbol is an object instance."""
        return (
            self.symbol_type == SymbolType.OBJECT_INSTANCE
            and self.instance_scope is not None
        )

    def is_closure(self) -> bool:
        """Check if this symbol is a closure with captured environment."""
        return (
            self.symbol_type == SymbolType.CAPTURED_CLOSURE
            and self.captured_frame is not None
        )

    @property
    def qualified_name(self) -> str:
        """Returns the fully qualified name of this symbol."""
        return f"{self.defining_scope.qualified_name}.{self.name}"

    def resolve_immediate(self) -> "Symbol":
        """
        Resolves to the immediate target of this symbol.
        If this symbol is an alias, returns what it's assigned to.
        Otherwise, returns itself.
        """
        return self.assigned_to if self.assigned_to else self

    def resolve_final(self, visited: Optional[Set["Symbol"]] = None) -> "Symbol":
        """
        Recursively resolves to the final target symbol.
        For functions/classes, resolves to themselves.
        For variables, follows assignment chain to the final function/class or returns None equivalent.
        """
        if visited is None:
            visited = set()

        if self in visited:
            raise RecursionError(
                f"Circular assignment detected for symbol '{self.name}'"
            )

        visited.add(self)

        # If this is a function or class, it resolves to itself (final)
        if self.symbol_type in (SymbolType.FUNCTION, SymbolType.CLASS):
            return self

        # If this symbol has an assignment, follow the chain
        if self.assigned_to:
            return self.assigned_to.resolve_final(visited)
        if self.assigned_to == None and self.symbol_type == SymbolType.PARAMETER:
            if self.name == "self":
                return self
            return None

        # For other types with no assignment, return self (could represent None/unknown)
        return self

    def assign_to(self, target: "Symbol"):
        """Creates an assignment relationship: self -> target"""
        if self.assigned_to:
            # Remove from previous target's assigned_from set
            self.assigned_to.assigned_from.discard(self)

        self.assigned_to = target
        target.assigned_from.add(self)

    def __repr__(self):
        assignment_info = (
            f" -> {self.assigned_to.qualified_name}" if self.assigned_to else ""
        )
        return f"<Symbol(name='{self.name}', type='{self.symbol_type.value}'{assignment_info})>"
