import ast
from pathlib import Path


class DetailVisitor(ast.NodeVisitor):
    def __init__(self, file_id: str, project_path: str):
        self.file_id = file_id
        self.project_path = project_path
        

    def visit_Import(self, node):
        for alias in node.names:
            pass

    def visit_ImportFrom(self, node):
        module_name = node.module
        if module_name:
            module_path = Path(self.project_path) / module_name
            if module_path.exists():
                pass
        else:
            pass

    