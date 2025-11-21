# storage/resolvers/execution_resolver.py
"""
ExecutionResolver - Context-sensitive symbol resolution during execution.
Port of the legacy ExecutionContextResolver to use database-backed queries.
Part of the Resolver Layer in the call graph architecture.
"""

from typing import Optional

from .scope_resolver import ScopeResolver
from .symbol_resolver import SymbolResolver
from app.core.parser.scope_manager.storage.repository.repos import ScopeManagerRepository
from app.core.parser.scope_manager.storage.models import SymbolModel


class ExecutionResolver:
    """
    Provides context-sensitive symbol resolution that considers:
    1. Execution scope locals (parameters and local variables)
    2. Closure captures (variables from parent frames)
    3. Instance attributes (for method calls)
    4. Lexical scope (LEGB fallback)
    """

    def __init__(
        self,
        repo: ScopeManagerRepository,
        scope_resolver: ScopeResolver,
        symbol_resolver: SymbolResolver
    ):
        self.repo = repo
        self.scope_resolver = scope_resolver
        self.symbol_resolver = symbol_resolver

    def resolve_in_frame(
        self,
        name: str,
        frame_id: str
    ) -> Optional[SymbolModel]:
        """
        Resolve a symbol in the execution context of a specific frame.

        Uses multiple strategies in order:
        1. Local variables in execution scope
        2. Closure captures (if function is a closure)
        3. Instance attributes (if this is a method call)
        4. Lexical scope (LEGB resolution)

        Args:
            name: Symbol name to resolve
            frame_id: ID of the call frame providing context

        Returns:
            Resolved symbol or None
        """
        frame = self.repo.call_frames.get_by_id(frame_id)
        if not frame:
            return None

        # Strategy 1: Check execution scope locals (args + local vars)
        local_symbol = self._resolve_local(name, frame.execution_scope_id)
        if local_symbol:
            return local_symbol

        # Strategy 2: Check closure captures
        closure_symbol = self._resolve_closure_capture(name, frame)
        if closure_symbol:
            return closure_symbol

        # Strategy 3: Check instance attributes (if method call)
        instance_symbol = self._resolve_instance_attribute(name, frame)
        if instance_symbol:
            return instance_symbol

        # Strategy 4: Fall back to lexical resolution
        return self._resolve_lexical(name, frame.callee_symbol_id)

    def _resolve_local(
        self,
        name: str,
        execution_scope_id: str
    ) -> Optional[SymbolModel]:
        """
        Strategy: Check execution scope for local variables and parameters.
        """
        return self.repo.symbols.get_by_name_in_scope(name, execution_scope_id)

    def _resolve_closure_capture(
        self,
        name: str,
        frame
    ) -> Optional[SymbolModel]:
        """
        Strategy: Walk captured frames to find variables.

        If the callee is a closure (has captured_frame_id), recursively
        resolve in the captured frame's context.
        """
        callee_symbol = self.repo.symbols.get_by_id(frame.callee_symbol_id)
        if not callee_symbol:
            return None

        # Check if callee is a closure
        if callee_symbol.captured_frame_id:
            # Recursively resolve in captured frame
            return self.resolve_in_frame(name, callee_symbol.captured_frame_id)

        return None

    def _resolve_instance_attribute(
        self,
        name: str,
        frame
    ) -> Optional[SymbolModel]:
        """
        Strategy: Check instance attributes for method calls.

        If this frame has a 'self' parameter (method call), check:
        1. Instance scope for instance attributes
        2. Class scope (via MRO) for class attributes
        """
        # Get 'self' parameter from execution scope
        self_symbol = self.repo.symbols.get_by_name_in_scope(
            'self',
            frame.execution_scope_id
        )

        if not self_symbol or not self_symbol.instance_scope_id:
            return None

        # Check instance scope first
        instance_attr = self.repo.symbols.get_by_name_in_scope(
            name,
            self_symbol.instance_scope_id
        )
        if instance_attr:
            return instance_attr

        # Check class scope (through MRO if available)
        instance_scope = self.repo.scopes.get_by_id(
            self_symbol.instance_scope_id)
        if not instance_scope or not instance_scope.parent_id:
            return None

        # The instance scope's parent is the class scope
        class_scope_id = instance_scope.parent_id

        # Try to resolve through class hierarchy
        # First direct lookup
        class_attr = self.repo.symbols.get_by_name_in_scope(
            name, class_scope_id)
        if class_attr:
            return class_attr

        # TODO: Could use InheritanceResolver here for full MRO lookup
        # For now, just check direct class scope
        return None

    def _resolve_lexical(
        self,
        name: str,
        callee_symbol_id: str
    ) -> Optional[SymbolModel]:
        """
        Strategy: LEGB resolution from function's definition point.

        Start from the scope where the function is defined and walk up
        the parent chain using standard LEGB rules.
        """
        callee_symbol = self.repo.symbols.get_by_id(callee_symbol_id)
        if not callee_symbol:
            return None

        # Start from the scope where the function is defined
        defining_scope_id = callee_symbol.defining_scope_id

        # Use LEGB resolution from this starting point
        return self.scope_resolver.resolve_name(name, defining_scope_id)

    def resolve_closure_variable(
        self,
        closure_symbol_id: str,
        variable_name: str
    ) -> Optional[SymbolModel]:
        """
        Resolve a variable captured by a closure.

        Args:
            closure_symbol_id: ID of the closure symbol
            variable_name: Name of the captured variable

        Returns:
            The captured variable symbol or None
        """
        closure_symbol = self.repo.symbols.get_by_id(closure_symbol_id)
        if not closure_symbol or not closure_symbol.captured_frame_id:
            return None

        # Resolve in the captured frame's context
        return self.resolve_in_frame(variable_name, closure_symbol.captured_frame_id)
