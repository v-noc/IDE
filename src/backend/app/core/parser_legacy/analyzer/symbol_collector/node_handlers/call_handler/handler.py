from typing import Callable, Optional
from contextlib import contextmanager


from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.model.base import BaseNode
from app.core.parser.scope_manager.core.symbol import Symbol, SymbolType
from app.core.parser.scope_manager.core.scope import ScopeType
from app.core.model.properties import CodePosition
from app.core.parser.ast.models import CallSchema

from .function_executor import FunctionExecutor
from .symbol_resolver import ResolutionResult, SymbolResolver


class CallCycleDetected(Exception):
    pass


class CallHandler:
    """Handles call-related nodes"""

    def __init__(
        self,
        symbol_table: SymbolTable,
        analyzer_callback: Callable[[BaseNode], None],
    ):
        self.symbol_table = symbol_table
        self.resolver = SymbolResolver(symbol_table.scope_manager)
        self.executor = FunctionExecutor(
            symbol_table.scope_manager, analyzer_callback, symbol_table
        )

    def handle_call(self, node: CallSchema) -> Optional[Symbol]:
        # Nested call case: if func itself is a call, attempt execution result
        if isinstance(node.func, CallSchema):
            inner_symbol = self.handle_call(node.func)

            if inner_symbol:
                # Re-run with the resolved callable symbol
                final_inner = inner_symbol.resolve_final()
                callee_result = ResolutionResult(symbol=final_inner)
                position = CodePosition(
                    line_no=node.position.line_no,
                    col_offset=node.position.col_offset,
                    end_line_no=node.position.end_line_no,
                    end_col_offset=node.position.end_col_offset,
                )

                if final_inner.symbol_type in (
                    SymbolType.FUNCTION,
                    SymbolType.CAPTURED_CLOSURE,
                ):
                    try:
                        with self._call_node_context(final_inner, position):
                            return self.executor.execute(
                                callee_result,
                                node.args,
                                node.keywords,
                            )
                    except CallCycleDetected:
                        return None

                if final_inner.symbol_type == SymbolType.CLASS:
                    return self.executor.instantiate_class(
                        final_inner, node.args, node.keywords
                    )

        callee_result = self.resolver.resolve_expression(node.func)
        if not callee_result or not callee_result.symbol:
            return None

        final_callee = callee_result.symbol.resolve_final()
        # callee_result.symbol = final_callee

        # Class instantiation
        if final_callee.symbol_type == SymbolType.CLASS:
            # Resolve __init__ and, if present, call it with instance bound
            # as self
            init_symbol = self.symbol_table.scope_manager.resolve_method(
                final_callee.qualified_name,
                "__init__",
            )
            if init_symbol:
                position = CodePosition(
                    line_no=node.position.line_no,
                    col_offset=node.position.col_offset,
                    end_line_no=node.position.end_line_no,
                    end_col_offset=node.position.end_col_offset,
                )
                try:
                    with self._call_node_context(init_symbol, position):
                        return self.executor.instantiate_class(
                            callee_result.symbol, node.args, node.keywords
                        )
                except CallCycleDetected:
                    return None

        # Regular function or closure execution
        if final_callee.symbol_type in (
            SymbolType.FUNCTION,
            SymbolType.CAPTURED_CLOSURE,
        ):
            position = CodePosition(
                line_no=node.position.line_no,
                col_offset=node.position.col_offset,
                end_line_no=node.position.end_line_no,
                end_col_offset=node.position.end_col_offset,
            )
            try:
                with self._call_node_context(final_callee, position):
                    return self.executor.execute(
                        callee_result,
                        node.args,
                        node.keywords,
                    )
            except CallCycleDetected:
                return None

        return None

    @contextmanager
    def _call_node_context(
        self,
        callee_symbol: Symbol,
        position: CodePosition,
    ):
        """Context manager to create, register, and cleanup a call node.

        Ensures the call node is added to the correct parent (scope or
        last call), pushed onto the call stack, and then popped on exit.
        """
        call_service = self.symbol_table.node_service["call"]

        parent_qname = self.symbol_table.scope_manager.current_scope.qualified_name
        parent_node = self.symbol_table.qname_to_node[parent_qname]
        if len(self.symbol_table.call_node_stack) > 0:
            parent_node = self.symbol_table.call_node_stack[-1]

        callee_node = self.symbol_table.qname_to_node[callee_symbol.qualified_name]
        parent_service = self.symbol_table.node_service[parent_node.node_type]

        # Detect recursive/cyclic calls using callee symbol identity (id/qname)
        # Prefer runtime call stack from the call tracker if available
        call_tracker = getattr(
            self.symbol_table.scope_manager, "call_tracker", None)

        if call_tracker and getattr(call_tracker, "call_stack", None):
            if any(
                getattr(frame.callee_symbol, "id", None) == callee_symbol.id
                or getattr(frame.callee_symbol, "qualified_name", None)
                == callee_symbol.qualified_name
                for frame in call_tracker.call_stack
            ):
                raise CallCycleDetected(
                    f"Call cycle detected: {callee_symbol.qualified_name}"
                )

        # Record the intent that this parent directly calls the target
        self.symbol_table.register_direct_call(parent_node.id, callee_node.id)

        # Try to reuse an existing call under this parent
        # targeting the same callee
        existing_call = call_service.get_call_with_parent_and_target(
            parent_node.id,
            callee_node.id,
        )
        if existing_call:
            self.symbol_table.call_node_stack.append(existing_call)
            try:
                yield existing_call
            finally:
                self.symbol_table.call_node_stack.pop()
            return

        # Adjust display name: prefix class for methods -> (ClassName).method
        display_name = callee_symbol.name
        try:
            defining_scope = getattr(callee_symbol, "defining_scope", None)
            if (
                defining_scope
                and getattr(defining_scope, "scope_type", None) == ScopeType.CLASS
            ):
                display_name = f"({defining_scope.name}).{callee_symbol.name}"
        except Exception:
            # Fallback to basic name if any metadata is missing
            display_name = callee_symbol.name

        call_node = call_service.create(
            name=display_name,
            qname=(
                f"{callee_symbol.qualified_name}L{position.line_no}"
                f"C{position.col_offset}"
            ),
            description=f"{display_name} function",
            position=position,
            target_id=callee_node.id,
        )
        self.symbol_table.call_node_stack.append(call_node)
        parent_service.add_call(parent_node.id, call_node.id)
        try:
            yield call_node
        except Exception as e:
            print(f"Error in call node context: {e}")
        finally:
            self.symbol_table.call_node_stack.pop()
