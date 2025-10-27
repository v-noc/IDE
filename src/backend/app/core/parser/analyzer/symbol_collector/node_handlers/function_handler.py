from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.parser.ast.models import FunctionSchema
from app.core.parser.scope_manager.core.symbol import SymbolType
from app.core.model.properties import CodePosition
from app.core.parser.scope_manager.core.scope import ScopeType


class FunctionHandler:
    """Handles function-related nodes"""

    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table

    def handle_function_node(self, node: FunctionSchema):
        """Register function schema and define argument symbols with
        resolved types.
        """
        current_scope = (
            self.symbol_table.scope_manager.current_scope.qualified_name
        )
        name_node = node.name
        parent_qname = (
            self.symbol_table.scope_manager.current_scope.parent
            .qualified_name
        )
        parent_node = self.symbol_table.qname_to_node[parent_qname]
        function_service = self.symbol_table.node_service["function"]

        if node.is_virtual:
            code_position = CodePosition(
                line_no=0, col_offset=0, end_line_no=0, end_col_offset=0
            )
        else:
            code_position = CodePosition(
                line_no=node.position.line_no,
                col_offset=node.position.col_offset,
                end_line_no=node.position.end_line_no,
                end_col_offset=node.position.end_col_offset,
            )

        function_node = None
        if not node.is_virtual and node.id:
            try:
                fetched = function_service.get(node.id)
                if fetched and getattr(fetched, "node_type", None) == \
                        "function":
                    function_node = fetched
                    function_node.position = code_position
                    function_service.update(function_node)
                else:
                    _key = node.id
                    function_node = function_service.create(
                        _key=_key,
                        name=name_node,
                        qname=current_scope,
                        description=f"{name_node} function",
                        position=code_position,
                    )

                    parent_function_service = self.symbol_table.node_service[
                        parent_node.node_type
                    ]
                    parent_function_service.add_function(
                        parent_node.id, function_node.id)

            except Exception:
                function_node = None

        if function_node is None:
            function_node = function_service.create(
                name=name_node,
                qname=current_scope,
                description=f"{name_node} function",
                position=code_position,
            )

            parent_service = self.symbol_table.node_service[
                parent_node.node_type
            ]
            parent_service.add_function(parent_node.id, function_node.id)

        self.symbol_table.qname_to_node[current_scope] = function_node

        # Define argument symbols with resolved types
        for arg in node.args:
            arg_name = arg.name

            self.symbol_table.scope_manager.define_symbol(
                arg_name,
                SymbolType.PARAMETER,
            )

        self.symbol_table.qname_to_function_node[current_scope] = node
