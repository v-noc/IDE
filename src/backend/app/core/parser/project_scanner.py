# src/backend/app/core/parser/project_scanner.py
import os
from typing import Dict, Any, Set
from .file_navigator import FileNavigator
from .python.ast_cache import ASTCache
from .python.symbol_table import SymbolTable
from .python.file_parser import PythonFileParser
from ..manager import CodeGraphManager
from ..tree_builder import build_tree_from_paths
from ...db import collections
from ...models.edges import BelongsToEdge, ContainsEdge, UsesImportEdge
from ...models.node import PackageNode
from ...models.properties import PackageProperties


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
        self.created_packages: Set[str] = set()

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

    def _create_package_node(self, package_qname: str) -> str:
        """
        Creates a PackageNode for an external package.
        
        Args:
            package_qname: The fully qualified name of the package
            
        Returns:
            The database ID of the created package node
        """
        if package_qname in self.created_packages:
            return self.symbol_table.get_symbol_id(package_qname)
        
        # Create the package node
        package_node = PackageNode(
            name=package_qname.split('.')[-1],  # Last part as name
            qname=package_qname,
            properties=PackageProperties()
        )
        
        # Save to database
        created_package = collections.nodes.create(package_node)
        
        # Update symbol table
        self.symbol_table.add_symbol(package_qname, created_package.id)
        
        # Link package to project with BelongsToEdge
        belongs_to_edge = BelongsToEdge(
            _from=created_package.id,
            _to=self.project.id
        )
        collections.belongs_to_edges.create(belongs_to_edge)
        
        # Mark as created
        self.created_packages.add(package_qname)
        
        return created_package.id

    def _process_dependency_edges(self, edges: list) -> None:
        """
        Processes the dependency edges from the detail pass, creating 
        package nodes as needed and linking them properly.
        
        Args:
            edges: List of UsesImportEdge models with target_qname metadata
        """
        for edge in edges:
            if not isinstance(edge, UsesImportEdge):
                continue
                
            target_qname = edge.target_qname
            if not target_qname:
                continue
            
            # Check if it's a local module or external package
            is_local = self.symbol_table.is_local_module(target_qname)
            
            if is_local:
                # It's a local module - find the existing node ID
                target_id = self.symbol_table.get_symbol_id(target_qname)
                if target_id:
                    edge.to_id = target_id
                    collections.uses_import_edges.create(edge)
                else:
                    print(f"Warning: Local module {target_qname} not found")
            else:
                # It's an external package - create package node if needed
                package_id = self._create_package_node(target_qname)
                edge.to_id = package_id
                collections.uses_import_edges.create(edge)

    def scan(self) -> None:
        """
        Orchestrates the entire scanning process for a project.
        This now includes Phase 2: Dependency and Import Resolution.
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

        # Third Pass: Phase 2 - Process dependencies and imports
        print("Processing dependencies and imports...")
        for file_path in py_files:
            # Get the file qname and find the corresponding file node
            file_qname = self.get_file_qname_from_path(file_path)
            file_node_id = self.symbol_table._qname_to_id.get(file_qname)
            
            if not file_node_id:
                continue
                
            # Run the detail pass to get dependency edges
            dependency_edges = self.file_parser.run_detail_pass(
                file_path, file_node_id
            )
            
            # Process the edges, creating package nodes as needed
            self._process_dependency_edges(dependency_edges)

        print(
            f"Project scan complete. "
            f"Processed {len(py_files)} files, "
            f"created {len(self.created_packages)} package nodes."
        )
    
    def get_scan_summary(self) -> Dict[str, Any]:
        """
        Returns a summary of the scanning results.
        
        Returns:
            Dictionary containing scan statistics and information
        """
        return {
            "project_path": self.project_path,
            "project_id": (
                self.project.id 
                if hasattr(self, 'project') else None
            ),
            "total_symbols": len(self.symbol_table._qname_to_id),
            "created_packages": list(self.created_packages),
            "cached_files": (
                len(self.ast_cache._cache) 
                if hasattr(self.ast_cache, '_cache') else 0
            )
        }
