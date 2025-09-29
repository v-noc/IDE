from typing import Callable, Optional
from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.parser.ast.models import CallSchema
from app.core.model.base import BaseNode
from app.core.model.nodes import CallNode
from app.core.parser.scope_manager.core.symbol import Symbol, SymbolType
from app.core.model.properties import CodePosition
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
            call_service = self.symbol_table.node_service['call']
            position = CodePosition(
                line_no=node.position.line_no,
                col_offset=node.position.col_offset,
                end_line_no=node.position.end_line_no,
                end_col_offset=node.position.end_col_offset
            )
            parent_qname = self.symbol_table.scope_manager.current_scope.qualified_name
            parent_node = self.symbol_table.qname_to_node[parent_qname]

            if len(self.symbol_table.call_node_stack) > 0:
                parent_node = self.symbol_table.call_node_stack[-1]

            callee_node = self.symbol_table.qname_to_node[callee_result.symbol.qualified_name]
            parent_service = self.symbol_table.node_service[parent_node.node_type]
            call_node = call_service.create(
                name=callee_result.symbol.name,
                qname=f"{callee_result.symbol.qualified_name}L{position.line_no}C{position.col_offset}",
                description=f"{callee_result.symbol.name} function",
                position=position,
                target_id=callee_node.id
            )
            self.symbol_table.call_node_stack.append(call_node)
            parent_service.add_call(parent_node.id, call_node.id)
            result = self.executor.execute(
                callee_result, node.args, node.keywords
            )
            self.symbol_table.call_node_stack.pop()
            return result

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
