from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.parser.ast.models import ClassSchema
from app.core.model.properties import CodePosition
from app.core.model.nodes import ClassNode


class ClassHandler:
    """Handles class-related nodes"""

    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table

    def handle_inherit_class_node(self, node: ClassSchema):
        """Process a class node and set up inheritance"""
        print(f"Processing class node: {node.name}")

        # Register class schema
        # Shortcuts
        qname = self.symbol_table.scope_manager.current_scope.qualified_name
        class_service = self.symbol_table.node_service['class']
        class_node: ClassNode = class_service.get_by_qname(qname)

        if class_node is None:
            return

        scope_manager = self.symbol_table.scope_manager

        classes = []
        for implemented_base in node.implements:
            resolved_base_qname = scope_manager.resolve_symbol_in_context(
                implemented_base.name)
            if not resolved_base_qname:
                continue
            classes.append(resolved_base_qname.qualified_name)

        scope_manager.register_class(classes)

        # Populate inherited members
        scope_manager.calculate_all_mro()

        class_node.implements = classes
        class_service.update(class_node)

    def handle_class_node(self, node: ClassSchema):
        """Process a class node and set up inheritance"""
        print(f"Processing class node: {node.name}")

        # Register class schema
        qname = self.symbol_table.scope_manager.current_scope.qualified_name
        parent_qname = self.symbol_table.scope_manager.current_scope.parent.qualified_name
        parent_node = self.symbol_table.qname_to_node[parent_qname]
        class_name = node.name

        code_position = CodePosition(
            line_no=node.position.line_no,
            col_offset=node.position.col_offset,
            end_line_no=node.position.end_line_no,
            end_col_offset=node.position.end_col_offset
        )

        class_node = self.symbol_table.node_service['class'].create(
            name=class_name,
            qname=qname,

            description=f"{class_name} function",
            position=code_position
        )
        print(f"Class node: {class_node}")
        self.symbol_table.qname_to_node[qname] = class_node

        parent_service = self.symbol_table.node_service[parent_node.node_type]
        parent_service.add_class(parent_node.id, class_node.id)
