# src/backend/app/core/parser/project_scanner.py
import os
from typing import Dict, Any
from .file_navigator import FileNavigator
from .python.ast_cache import ASTCache
from .python.symbol_table import SymbolTable
from .python.file_parser import PythonFileParser
from ..manager import CodeGraphManager
from ..tree_builder import build_tree_from_paths
from ...db import collections
from ...models.edges import BelongsToEdge, ContainsEdge
from ...models.node import NodePosition


class ProjectScanner:
    """
    The main entry point and orchestrator for parsing a whole project using
    the advanced two-pass analysis system.
    """
    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(project_path)
        self.file_navigator = FileNavigator(
            self.project_path, "v-noc.toml"
        )
        self.ast_cache = ASTCache()
        self.symbol_table = SymbolTable()
        self.file_parser = PythonFileParser(
            self.ast_cache, self.symbol_table, self.project_path
        )
        self.code_graph_manager = CodeGraphManager()

    def create_nodes_and_edges_from_tree(
        self, 
        tree: Dict[str, Any], 
        parent_node, 
        parent_path: str
    ) -> None:
        """
        Recursively creates folder and file nodes from the tree structure
        and links them with ContainsEdge and BelongsToEdge.
        """
        for name, subtree in tree.items():
            current_path = os.path.join(parent_path, name)
            
            if subtree is None:
                # It's a file - create FileNode
                file_qname = current_path.replace(
                    self.project_path, ""
                ).lstrip("/").replace(".py", "").replace("/", ".")
                
                file_node = parent_node.add_file(
                    file_name=name,
                    file_path=current_path
                )
                
                # Link file to project with BelongsToEdge
                belongs_to_edge = BelongsToEdge(
                    _from=file_node.id,
                    _to=self.project.id
                )
                collections.belongs_to_edges.create(belongs_to_edge)
                
                # Add to symbol table
                self.symbol_table.add_symbol(file_qname, file_node.id)
                
            else:
                # It's a folder - create FolderNode
                folder_qname = current_path.replace(
                    self.project_path, ""
                ).lstrip("/").replace("/", ".")
                
                folder_node = parent_node.add_folder(
                    folder_name=name,
                    folder_path=current_path
                )
                
                # Link folder to project with BelongsToEdge
                belongs_to_edge = BelongsToEdge(
                    _from=folder_node.id,
                    _to=self.project.id
                )
                collections.belongs_to_edges.create(belongs_to_edge)
                
                # Add to symbol table
                self.symbol_table.add_symbol(folder_qname, folder_node.id)
                
                # Recurse for subdirectories
                self.create_nodes_and_edges_from_tree(
                    subtree, folder_node, current_path
                )

    def get_file_qname_from_path(self, file_path: str) -> str:
        """
        Generate the file qname from file path using the same pattern.
        """
        return file_path.replace(
            self.project_path, ""
        ).lstrip("/").replace(".py", "").replace("/", ".")

    def scan(self) -> None:
        """
        Orchestrates the entire scanning process for a project.
        """
        # Create the main project using CodeGraphManager
        project_name = os.path.basename(self.project_path)
        self.project = self.code_graph_manager.create_project(
            name=project_name,
            path=self.project_path
        )
        
        # Add project to symbol table
        self.symbol_table.add_symbol(self.project.name, self.project.id)

        # First Pass: Build folder/file hierarchy
        py_files = self.file_navigator.find_files(extensions=[".py"])
        
        # Build tree structure from file paths
        tree = build_tree_from_paths(py_files, self.project_path)
        
        # Create folder and file nodes with proper edges
        self.create_nodes_and_edges_from_tree(
            tree, self.project, self.project_path
        )

        # Second Pass: Process declarations for each Python file
        for file_path in py_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                continue

            # Get the file qname and find the corresponding file node
            file_qname = self.get_file_qname_from_path(file_path)
            file_node_id = self.symbol_table._qname_to_id.get(file_qname)
            
            if not file_node_id:
                print(f"Warning: Could not find file node for {file_path}")
                continue

            declared_nodes = self.file_parser.run_declaration_pass(
                file_path, content
            )
            for node in declared_nodes:
                created_node = collections.nodes.create(node)
                self.symbol_table.add_symbol(
                    created_node.qname, created_node.id
                )
                
                # Link declared nodes to their file with ContainsEdge
                contains_edge = ContainsEdge(
                    _from=file_node_id,
                    _to=created_node.id,
                    position=node.properties.position
                )
                collections.contains_edges.create(contains_edge)
                
                # Link declared nodes to project with BelongsToEdge
                belongs_to_edge = BelongsToEdge(
                    _from=created_node.id,
                    _to=self.project.id
                )
                collections.belongs_to_edges.create(belongs_to_edge)

        # Third Pass (to be implemented)
        # for file_path in py_files:
        #     edge_models = self.file_parser.run_detail_pass(file_path)
        #     for edge in edge_models:
        #         collections.edges.create(edge)

        print(
            "Project scan complete. "
            "Folder hierarchy and declarations processed."
        )
