from copy import deepcopy
from typing import Dict, Any, List, Optional
from typing import TYPE_CHECKING
from .models import CallGraph, CallFrame, CallSite
import uuid
from app.core.parser.scope_manager.core import Scope, ScopeType, SymbolType, Symbol
if TYPE_CHECKING:
    from app.core.parser.scope_manager.manager import ScopeManager


# TODO: Fix recursive check
class CallGraphTracker:
    """
    Tracks the call graph and manages the call stack.
    """

    def __init__(self, scope_manager: "ScopeManager"):
        self.scope_manager = scope_manager
        self.call_graph = CallGraph()
        self.max_recursion_depth = 100

    @property
    def current_frame(self) -> Optional[CallFrame]:
        """Get the currently active call frame."""
        return self.call_graph.active_frames[-1] if self.call_graph.active_frames else None

    @property
    def call_stack(self) -> List[CallFrame]:
        """Get the current call stack."""
        return self.call_graph.active_frames

    def start_call(self, callee_symbol: Symbol, args: Dict[str, Any]):
        """
        Start a new function call. This is the core entry point.
        """
        # 1. Recursion protection
        if len(self.call_stack) >= self.max_recursion_depth:
            raise RecursionError(
                f"Maximum call depth exceeded: {self.max_recursion_depth}")

        # 2. Resolve the final callable target (follow aliases)
        final_callee = callee_symbol.resolve_final()

        # 3. Create unique execution scope for this call
        execution_scope = self._create_execution_scope(final_callee)

        # 4. Create CallFrame (with call_site=None initially to avoid circular dependency)
        frame = CallFrame(
            id=str(uuid.uuid4()),
            callee_symbol=final_callee,
            execution_scope=execution_scope,
            parent_frame=self.current_frame,
            call_site=None  # Will be set after CallSite creation
        )

        # 5. Create CallSite with the previous frame (if any)
        previous_frame = self.current_frame
        call_site = CallSite(
            caller_frame=previous_frame if previous_frame else frame,
            callee_symbol=final_callee,

        )

        frame.call_site = call_site

        # 7. Populate execution scope with arguments
        self._populate_arguments(frame, args)

        # 8. Update call stack
        self.call_graph.active_frames.append(frame)

        # 9. Update call graph
        if previous_frame is not None:
            # Normal nested call: record caller -> callee
            self.call_graph.add_call(call_site)
        else:
            # Root-level call: attribute it to the module scope
            module_qname = self.scope_manager.current_scope.qualified_name
            if module_qname not in self.call_graph.edges:
                self.call_graph.edges[module_qname] = []
            self.call_graph.edges[module_qname].append(call_site)

        return frame

    def end_call(self, return_value: Optional[Symbol] = None) -> Optional[Symbol]:
        """
        End the current function call.

        Handles the CRITICAL closure capture logic and pops the frame
        """

        if not self.call_stack:
            raise RuntimeError("No active call to end")

        # 1. Pop the completed frame
        completed_frame = self.call_graph.active_frames.pop()

        if return_value:
            return_value = Symbol(
                is_runtime=True,
                **return_value.model_dump(exclude={"is_runtime"})
            )
            return_value.bind_table(self.scope_manager.table)
            self.scope_manager.table.save_symbol(return_value)

        # 2. CRITICAL CLOSURE LOGIC:
        # If returning a function, stamp it with the captured frame
        processed_return = self._process_return_value(
            return_value, completed_frame)

        # 3. Store return value on the frame
        completed_frame.return_value = processed_return

        # if processed_return is None or processed_return.symbol_type != SymbolType.CAPTURED_CLOSURE and processed_return.symbol_type != SymbolType.OBJECT_INSTANCE:
        # completed_frame.execution_scope.symbols.clear()

        return processed_return

    def _create_execution_scope(self, calle_symbol: Symbol) -> Scope:
        """Create a unique execution scope for a function call."""

        scope_name = f'exec_{calle_symbol.name}_{uuid.uuid4().hex[:8]}'

        execution_scope = Scope(
            id=str(uuid.uuid4()),
            name=scope_name,
            scope_type=ScopeType.EXECUTION,
            parent_id=calle_symbol.defining_scope.id
        )

        execution_scope.bind_table(self.scope_manager.table)
        self.scope_manager.table.save_scope(execution_scope)

        return execution_scope

    def _populate_arguments(self, frame: CallFrame, arguments: Dict[str, Any]):
        """Populate the execution scope with function arguments.

        Always create parameter symbols in the execution scope. If an argument
        value is a symbol, link via assignment rather than inserting the
        external symbol into this scope.
        """

        for param_name, arg_value in arguments.items():
            # Create a parameter symbol local to the execution scope
            param_symbol = Symbol(
                name=param_name,
                is_runtime=True,
                symbol_type=SymbolType.PARAMETER,
                defining_scope_id=frame.execution_scope.id
            )
            param_symbol.bind_table(self.scope_manager.table)
            self.scope_manager.table.save_symbol(param_symbol)
            frame.execution_scope.add_symbol(param_symbol)

            # If the provided argument is a symbol, link it; otherwise
            # store the literal as metadata on the parameter symbol
            if isinstance(arg_value, Symbol):
                param_symbol.assign_to(arg_value)
            else:
                param_symbol.metadata["literal_value"] = arg_value

    def _process_return_value(self, return_value: Optional[Symbol], completed_frame: CallFrame) -> Optional[Symbol]:
        """Process return value and handle closure capture.

        This is WHERE THE MAGIC HAPPENS for higher-order functions.
        """
        if not return_value:
            return None

            # If returning a function, it becomes a closure
        if return_value.symbol_type == SymbolType.FUNCTION:

            # CRITICAL: Stamp the returned function with the captured frame
            return_value.captured_frame = completed_frame
            return_value.symbol_type = SymbolType.CAPTURED_CLOSURE

            # Debug output
            if hasattr(self.scope_manager, 'debug_mode') and self.scope_manager.debug_mode:
                print(
                    f"CLOSURE CAPTURED: {return_value.name} captures frame {completed_frame.id[:8]}")

        return return_value

    def get_call_depth(self) -> int:
        """Get current call stack depth."""
        return len(self.call_stack)

    def get_recent_calls(self, limit: int = 10) -> List[CallFrame]:
        """Get the most recent completed calls (for debugging)."""
        # This would require tracking completed calls, but keeping it simple for now
        return self.call_stack[-limit:] if self.call_stack else []
