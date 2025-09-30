from pathlib import Path
from typing import Optional
from .analyzer.file_navigator import FileNavigator
from .analyzer.symbol_analyzer import SymbolAnalyzer
from app.core.parser.ast.scanner import scan
from app.core.parser.analyzer.file_navigator import FileContainer
from arango.database import StandardDatabase


class GraphBuilder:
    def __init__(self, project_path: str, ignore_file_name: str, db: StandardDatabase):
        self.file_navigator = FileNavigator(project_path, ignore_file_name)
        self.symbol_analyzer = SymbolAnalyzer(db)
        self.file_containers = []

    def build(self, project_name: str, project_description: str):
        self.symbol_analyzer.create_project_node(
            project_name, project_description, str(self.file_navigator.root_path))

        py_files = self.file_navigator.find_files(extensions=[".py"])

        for file_path in py_files:
            with open(file_path, "r") as file:
                file_content = file.read()
                ast_scanner = scan(file_content)
                file_name = Path(file_path)

                relative_path = file_name.relative_to(
                    self.file_navigator.root_path)

                file_container = FileContainer(file_path=str(relative_path),
                                               file_name=file_name.stem, parsed_nodes=ast_scanner)

                self.symbol_analyzer.add_file(file_container)
                self.file_containers.append(file_container)

        self.symbol_analyzer.build_symbol_table()

        current_scope = self.symbol_analyzer.symbol_table.scope_manager.root_scope

        def print_scope(current, indent=0):

            for scope in current.children:
                print("  " * indent + current.children[scope].qualified_name)
                print_scope(current.children[scope], indent + 1)

        print_scope(current_scope, 0)
