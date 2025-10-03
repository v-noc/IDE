from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.parser.ast.models import ClassSchema, FunctionSchema
from app.core.model.properties import CodePosition
from app.core.model.nodes import ClassNode
from app.core.parser.scope_manager.core.scope import ScopeType
from app.core.parser.analyzer.symbol_collector.node_handlers.function_handler import (
    FunctionHandler,
)


class ClassHandler:
    """Handles class-related nodes"""

    def __init__(self, symbol_table: SymbolTable, function_handler: FunctionHandler):
        self.symbol_table = symbol_table
        self.function_handler = function_handler

    def handle_inherit_class_node(self, node: ClassSchema):
        """Process a class node and set up inheritance"""
        print(f"Processing class node: {node.name}")

        # Register class schema
        # Shortcuts
        qname = self.symbol_table.scope_manager.current_scope.qualified_name
        class_service = self.symbol_table.node_service["class"]
        class_node: ClassNode = class_service.get_by_qname(qname)

        if class_node is None:
            return

        scope_manager = self.symbol_table.scope_manager

        classes = []
        for implemented_base in node.implements:
            resolved_base_qname = scope_manager.resolve_symbol_in_context(
                implemented_base.name
            )
            if not resolved_base_qname:
                continue
            classes.append(resolved_base_qname.resolve_final().qualified_name)

        scope_manager.register_class(classes)

        # Populate inherited members
        scope_manager.calculate_all_mro()
        mro = scope_manager.get_mro(qname)
        init_symbol = scope_manager.resolve_method(qname, "__init__")
        if init_symbol is None:
            scope_manager.enter_scope("__init__", ScopeType.FUNCTION)
            function_schema = FunctionSchema(
                name="__init__", args=[], position=node.position
            )
            self.function_handler.handle_function_node(function_schema)
            scope_manager.exit_scope()

        class_node.implements = mro
        class_service.update(class_node)

    def handle_class_node(self, node: ClassSchema):
        """Process a class node and set up inheritance"""
        print(f"Processing class node: {node.name}")

        # Register class schema
        qname = self.symbol_table.scope_manager.current_scope.qualified_name
        parent_qname = (
            self.symbol_table.scope_manager.current_scope.parent.qualified_name
        )
        parent_node = self.symbol_table.qname_to_node[parent_qname]
        class_name = node.name

        code_position = CodePosition(
            line_no=node.position.line_no,
            col_offset=node.position.col_offset,
            end_line_no=node.position.end_line_no,
            end_col_offset=node.position.end_col_offset,
        )

        class_node = self.symbol_table.node_service["class"].create(
            name=class_name,
            qname=qname,
            description=f"{class_name} function",
            position=code_position,
        )
        print(f"Class node: {class_node}")
        self.symbol_table.qname_to_node[qname] = class_node

        parent_service = self.symbol_table.node_service[parent_node.node_type]
        parent_service.add_class(parent_node.id, class_node.id)
