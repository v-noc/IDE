from typing import Optional, TYPE_CHECKING
from app.core.parser.scope_manager.core.symbol import Symbol
from .models import CallFrame


class ExecutionContextResolver:
    """
    Provides context-sensitive symbol resolution that considers both
    """

    if TYPE_CHECKING:
        from app.core.parser.scope_manager.manager import ScopeManager

    def __init__(self, scope_manager: "ScopeManager"):
        self.scope_manager = scope_manager

    def resolve(self, name: str, frame: Optional[CallFrame] = None) -> Optional[Symbol]:
        """Resolve a symbol in the execution context."""
        if frame is None:
            frame = self.scope_manager.call_tracker.current_frame

        if not frame:
            return self.scope_manager.lookup_symbol(name)

        return self._resolve_with_context(name, frame)

    def _resolve_with_context(self, name: str, frame: CallFrame) -> Optional[Symbol]:
        """Resolve a symbol in the execution context."""
        # 1. Check frame's execution_scope.symbols (args + locals)
        if name in frame.execution_scope.symbols:
            return frame.execution_scope.symbols[name]

        # 2. If closure, recursively check captured_frame
        if frame.callee_symbol.is_closure():
            captured_result = self._resolve_closure_capture(name, frame)
            if captured_result:
                return captured_result

        # 3. Check instance variables (if we're in a method)
        self_symbol = frame.execution_scope.symbols.get("self")
        if self_symbol and self_symbol.is_instance():
            instance_result = self._resolve_instance_attribute(
                name, self_symbol)
            if instance_result:
                return instance_result

        # 4. Fall back to lexical resolution from function's definition point
        callee_scope = self.scope_manager.get_scope_by_qname(
            frame.callee_symbol.qualified_name)
        return self._resolve_lexical(name, callee_scope)

    def _resolve_closure_capture(self, name: str, frame: CallFrame):
        """Resolve variables captured in closures."""
        captured_frame = frame.callee_symbol.captured_frame
        if not captured_frame:
            return None

        return self.resolve(name, captured_frame)

    def _resolve_instance_attribute(self, name: str, instance_symbol: Symbol) -> Optional[Symbol]:
        """Resolve instance attributes."""
        if not instance_symbol.instance_scope:
            return None

        # Check instance scope
        if name in instance_symbol.instance_scope.symbols:
            return instance_symbol.instance_scope.symbols[name]

        # Check class attributes through existing MRO system
        if instance_symbol.instance_scope.parent:
            class_scope = instance_symbol.instance_scope.parent
            return class_scope.symbols.get(name)

        return None

    def _resolve_lexical(self, name: str, start_scope) -> Optional[Symbol]:
        """standard lexical resolution starting from a specific scope."""

        current_scope = start_scope
        while current_scope:
            # Direct symbol
            if name in current_scope.symbols:
                return current_scope.symbols[name]

            # Wildcard-imported module scopes (last-import wins)
            for module_scope in reversed(current_scope.wildcard_import_scopes):
                if name in module_scope.symbols:
                    return module_scope.symbols[name]

            current_scope = current_scope.parent

        return None
