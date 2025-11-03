from __future__ import annotations
from enum import Enum
import uuid
from ..storage.symbol_table import SymbolTable

from typing import TYPE_CHECKING, Optional, Dict, Any, Set
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .scope import Scope
    from .call_context.models import CallFrame


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

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # --- Core Identification ---
    name: str  # The name of the symbol, e.g., "my_variable"
    symbol_type: SymbolType

    # --- Definitional Context ---
    # A reference to the scope object where this symbol is defined.
    # This avoids storing scope IDs and allows direct traversal.
    defining_scope_id: str = Field(...)

    # code_position: CodePosition

    # --- Assignment Tracking ---
    # Tracks what this symbol is assigned to (for alias resolution)
    assigned_to_id: Optional[str] = Field(default=None)

    # Tracks what symbols are assigned to this symbol (reverse mapping)
    assigned_from_ids: Set[str] = Field(default_factory=set)

    # --- Flexible Metadata ---
    # A generic dictionary to hold extra information without cluttering the model.
    # This is where details like `is_async`, `decorators`, `base_classes`, etc., can be stored.
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # For closures: Link to the frame this function captured (kept as Any to avoid early import cycles)
    captured_frame: Optional[Any] = Field(
        default=None,  description="Frame this closure captured"
    )

    instance_scope_id: Optional[str] = Field(
        default=None,  description="Scope for object instance attributes"
    )

    # --- Runtime Context (not stored) ---
    _table: Optional[SymbolTable] = None

    # --- Caches ---
    _defining_scope_cache: Optional[Scope] = None
    _assigned_to_cache: Optional[Symbol] = None
    _instance_scope_cache: Optional[Scope] = None
    _captured_frame_cache: Optional[CallFrame] = None

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = False

    def bind_table(self, table: SymbolTable) -> Symbol:
        """Bind this symbol to a SymbolTable for relationship navigation."""
        self._table = table
        return self

    @property
    def defining_scope(self) -> Optional[Scope]:
        """Lazy-load the scope where this symbol is defined."""
        if not self._table:
            raise RuntimeError("Symbol must be bound to a SymbolTable")

        if self._defining_scope_cache is not None:
            return self._defining_scope_cache

        self._defining_scope_cache = self._table.get_scope(
            self.defining_scope_id)
        if self._defining_scope_cache:
            self._defining_scope_cache.bind_table(self._table)

        return self._defining_scope_cache

    def __hash__(self):
        # Unique identifier for a symbol is its name and the scope it's defined in.
        return hash((self.name, id(self.defining_scope)))

    def is_instance(self) -> bool:
        """Check if this symbol is an object instance."""
        return (
            self.symbol_type == SymbolType.OBJECT_INSTANCE
            and self.instance_scope_id is not None
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

    # @property
    # def captured_frame(self) -> Optional[CallFrame]:
    #     """Lazy-load the captured frame (for closures)."""
    #     if not self._table:
    #         raise RuntimeError("Symbol must be bound to a SymbolTable")

    #     if self._captured_frame_cache is not None:
    #         return self._captured_frame_cache

    #     if self.captured_frame_id:
    #         self._captured_frame_cache = self._table.get_call_frame(
    #             self.captured_frame_id)
    #         if self._captured_frame_cache:
    #             self._captured_frame_cache.bind_table(self._table)

    #     return self._captured_frame_cache

    @property
    def assigned_to(self) -> Optional[Symbol]:
        """Lazy-load the symbol this is assigned to."""
        if not self._table:
            raise RuntimeError("Symbol must be bound to a SymbolTable")

        if self._assigned_to_cache is not None:
            return self._assigned_to_cache

        if self.assigned_to_id:
            self._assigned_to_cache = self._table.get_symbol(
                self.assigned_to_id)
            if self._assigned_to_cache:
                self._assigned_to_cache.bind_table(self._table)

        return self._assigned_to_cache

    @property
    def instance_scope(self) -> Optional[Scope]:
        """Lazy-load the instance scope (for object instances)."""
        if not self._table:
            raise RuntimeError("Symbol must be bound to a SymbolTable")

        if self._instance_scope_cache is not None:
            return self._instance_scope_cache

        if self.instance_scope_id:
            self._instance_scope_cache = self._table.get_scope(
                self.instance_scope_id)
            if self._instance_scope_cache:
                self._instance_scope_cache.bind_table(self._table)

        return self._instance_scope_cache

    def resolve_final(self, visited: Optional[Set["Symbol"]] = None) -> "Symbol":
        """
        Follow the assignment chain to find the final target.
        Handles cycles gracefully.

        For functions/classes: returns itself (it's the final target)
        For variables: follows assignment chain
        For parameters: returns self if unassigned
        """
        if not self._table:
            raise RuntimeError("Symbol must be bound to a SymbolTable")

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

        # Follow assignment chain
        if self.assigned_to_id:
            next_symbol = self.assigned_to
            if next_symbol:
                return next_symbol.resolve_final(visited)

        # Special case for parameters
        if self.symbol_type == SymbolType.PARAMETER:
            if self.name == "self":
                return self
            return None

        # For other types with no assignment, return self
        return self

    def assign_to(self, target: Symbol):
        """
        Create an assignment relationship: self -> target.
        Updates both in-memory state and database.
        """
        if not self._table:
            raise RuntimeError("Symbol must be bound to a SymbolTable")

        self.assigned_to_id = target.id
        self._assigned_to_cache = target

        # Persist the change
        try:
            self._table.save_symbol(self)
        except Exception as e:
            print(f"Error saving symbol: {e}")

    def __repr__(self):
        assignment_info = (
            f" -> {self.assigned_to.qualified_name}" if self.assigned_to else ""
        )
        return f"<Symbol(name='{self.name}', type='{self.symbol_type.value}'{assignment_info})>"
