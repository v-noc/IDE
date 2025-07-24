import ast
import os
from pathlib import Path
from ..file_navigator import FileNavigator

class AdvancedCodeAnalyzer:
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.navigator = FileNavigator(self.project_path.resolve(), "v-noc.toml")
        self.tree = {}

    def analyze(self):
        python_files = self.navigator.find_files(extensions=['.py'])
        for file_path in python_files:
            with open(file_path, 'r') as file:
                code = file.read()

                file_path = os.path.relpath(file_path, self.project_path.resolve())
                file_name = os.path.basename(file_path)
                tree = ast.parse(code)

                print(file_name)
                print(tree)
    
    def build_tree_from_paths(self, path):
        parts = path.split('/')
        current = self.tree
        for i, part in enumerate(parts):
            if i == len(parts) - 1:  # It's a file
                current.setdefault(part, None)
            else:  # It's a folder
                current = current.setdefault(part, {})
       





                