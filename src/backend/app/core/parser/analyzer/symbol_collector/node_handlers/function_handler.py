from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.parser.ast.models import ArgSchema, FunctionSchema
from app.core.parser.scope_manager.core.symbol import SymbolType
from app.core.model.properties import CodePosition


class FunctionHandler:
    """Handles function-related nodes"""

    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table

    def handle_function_node(self, node: FunctionSchema):
        """Register function schema and define argument symbols with
        resolved types.
        """
        current_scope = self.symbol_table.scope_manager.current_scope.qualified_name
        name_node = node.name
        parent_qname = self.symbol_table.scope_manager.current_scope.parent.qualified_name
        parent_node = self.symbol_table.qname_to_node[parent_qname]

        code_position = CodePosition(
            line_no=node.position.line_no,
            col_offset=node.position.col_offset,
            end_line_no=node.position.end_line_no,
            end_col_offset=node.position.end_col_offset
        )

        function_node = self.symbol_table.node_service['function'].create(
            name=name_node,
            qname=current_scope,
            description="",
            position=code_position
        )

        self.symbol_table.qname_to_node[current_scope] = function_node
        parent_service = self.symbol_table.node_service[parent_node.node_type]
        parent_service.add_function(parent_node.id, function_node.id)

        # Define argument symbols with resolved types
        for arg in node.args:
            arg_name = arg.name

            self.symbol_table.scope_manager.define_symbol(
                arg_name,
                SymbolType.PARAMETER,
            )

        self.symbol_table.qname_to_function_node[current_scope] = node
