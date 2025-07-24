# src/backend/app/core/parser/project_scanner.py
import os
from .file_navigator import FileNavigator
from .python.ast_cache import ASTCache
from .python.symbol_table import SymbolTable
from .python.file_parser import PythonFileParser
from ...db import collections
from ...models.node import ProjectNode, FileNode, FolderNode
from ...models.properties import ProjectProperties, FileProperties

class ProjectScanner:
    """
    The main entry point and orchestrator for parsing a whole project using
    the advanced two-pass analysis system.
    """
    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(project_path)
        self.file_navigator = FileNavigator(self.project_path, "v-noc.toml")
        self.ast_cache = ASTCache()
        self.symbol_table = SymbolTable()
        self.file_parser = PythonFileParser(self.ast_cache, self.symbol_table, self.project_path)

    def scan(self) -> None:
        """
        Orchestrates the entire scanning process for a project.
        """
        # Create the main project node
        project_name = os.path.basename(self.project_path)
        project_node = ProjectNode(
            name=project_name,
            qname=project_name,
            properties=ProjectProperties(path=self.project_path)
        )
        created_project = collections.nodes.create(project_node)
        self.symbol_table.add_symbol(created_project.qname, created_project.id)

        # First Pass: Declarations
        py_files = self.file_navigator.find_files(extensions=[".py"])
        for file_path in py_files:
            # Create FileNode
            file_name = os.path.basename(file_path)
            file_qname = file_path.replace(self.project_path, "").lstrip("/").replace(".py", "").replace("/", ".")
            file_node = FileNode(
                name=file_name,
                qname=file_qname,
                properties=FileProperties(path=file_path)
            )
            created_file = collections.nodes.create(file_node)
            self.symbol_table.add_symbol(created_file.qname, created_file.id)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                continue

            declared_nodes = self.file_parser.run_declaration_pass(file_path, content)
            for node in declared_nodes:
                created_node = collections.nodes.create(node)
                self.symbol_table.add_symbol(created_node.qname, created_node.id)

        # Second Pass (to be implemented)
        # for file_path in py_files:
        #     edge_models = self.file_parser.run_detail_pass(file_path)
        #     for edge in edge_models:
        #         collections.edges.create(edge)

        print("Phase 1 scan complete. Declarations have been processed.")
