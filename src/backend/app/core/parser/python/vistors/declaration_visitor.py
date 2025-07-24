import ast
from app.models.node import NodePosition, ClassNode, FunctionNode
from app.models.properties import FunctionProperties, ClassProperties


class DeclarationVisitor(ast.NodeVisitor):
    def __init__(self, file_id: str):
        self.file_id = file_id
        

    def visit_FunctionDef(self, node):
        name = node.name
        node_position = NodePosition(
            line_no=node.lineno,
            col_offset=node.col_offset,
            end_line_no=node.end_lineno,
            end_col_offset=node.end_col_offset
        )
        function = FunctionNode(
            name=name,
            qname=name,
            node_type="function",
            properties=FunctionProperties(
                position=node_position,
              
            )
        )
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        name = node.name
        node_position = NodePosition(
            line_no=node.lineno,
            col_offset=node.col_offset,
            end_line_no=node.end_lineno,
            end_col_offset=node.end_col_offset
        )

        class_def = ClassNode(
            name=name,
            qname=name,
            node_type="class",
            properties=ClassProperties(
                position=node_position,
                fields=[]
            )
        )

        self.generic_visit(node)


