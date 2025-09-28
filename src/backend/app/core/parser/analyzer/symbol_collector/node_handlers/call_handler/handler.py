from typing import Callable, Optional
from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.parser.ast.models import CallSchema
from app.core.model.base import BaseNode
from app.core.model.nodes import CallNode
from app.core.parser.scope_manager.core.symbol import Symbol, SymbolType
from .function_executor import FunctionExecutor
from .symbol_resolver import SymbolResolver


class CallHandler:
    """Handles call-related nodes"""

    def __init__(self,
                 symbol_table: SymbolTable,
                 analyzer_callback: Callable[[BaseNode], None]):
        self.symbol_table = symbol_table
        self.resolver = SymbolResolver(symbol_table.scope_manager)
        self.executor = FunctionExecutor(
            symbol_table.scope_manager, analyzer_callback, symbol_table
        )

    def handle_call(self, node: CallNode) -> Optional[Symbol]:
        callee_result = self.resolver.resolve_expression(node.func)
        if not callee_result or not callee_result.symbol:
            return None

        final_callee = callee_result.symbol.resolve_final()
        callee_result.symbol = final_callee

        # Class instantiation
        if final_callee.symbol_type == SymbolType.CLASS:
            return self.executor.instantiate_class(
                final_callee, node.args, node.keywords
            )

        # Regular function or closure execution
        if final_callee.symbol_type in (
            SymbolType.FUNCTION,
            SymbolType.CAPTURED_CLOSURE,
        ):
            return self.executor.execute(
                callee_result, node.args, node.keywords
            )

        # Nested call case: if func itself is a call, attempt execution result
        if isinstance(node.func, CallNode):
            inner_symbol = self.handle_call(node.func)
            if inner_symbol:
                # Re-run with the resolved callable symbol
                callee_result.symbol = inner_symbol.resolve_final()
                return self.executor.execute(
                    callee_result, node.args, node.keywords
                )

        return None
