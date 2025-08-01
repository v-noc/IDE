# src/backend/app/core/parser/project_scanner.py
import os
from typing import Dict, Any
import ast

from app.db import collections
from app.models.edges import (
    BelongsToEdge, ContainsEdge, UsesImportEdge, CallEdge
)
from app.models.node import PackageNode
from app.core.project import Project
from app.models.properties import PackageProperties

from .file_navigator import FileNavigator
from .python.ast_cache import ASTCache
from .python.symbol_table import SymbolTable
from .python.file_parser import PythonFileParser
from ..manager import CodeGraphManager
from ..tree_builder import build_tree_from_paths


class ProjectScanner:
    """
    The main entry point and orchestrator for parsing a whole project using
    the advanced two-pass analysis system.
    """
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.file_navigator = FileNavigator(project_path)
        self.code_graph_manager = CodeGraphManager()
        self.file_parser = PythonFileParser(
            ast_cache=ASTCache(),
            symbol_table=SymbolTable(),
            project_root=project_path
        )
        self.symbol_table = self.file_parser.symbol_table
        self.created_packages: set = set()
        # Track package name -> ID mapping
        self.package_ids: Dict[str, str] = {}
        self.project = None
    
   
    def get_project(self) -> Project:
        return self.project

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
                
                # Make path relative to project
                relative_path = (current_path.replace(self.project_path, "")
                                 .lstrip("/"))
                
                file_node = parent_node.add_file(
                    file_name=name,
                    file_path=relative_path
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
                
                # Make path relative to project
                relative_path = (current_path.replace(self.project_path, "")
                                 .lstrip("/"))
                
                folder_node = parent_node.add_folder(
                    folder_name=name,
                    folder_path=relative_path
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
        # Check if we've already created this package
        if package_qname in self.package_ids:
            return self.package_ids[package_qname]
        
        # Determine the base package name (first part of qname)
        base_package = package_qname.split('.')[0]
        
        # Check if the base package has already been created
        if base_package in self.created_packages:
            # Find the existing package node
            existing_package = collections.nodes.find_one({
                "qname": base_package,
                "node_type": "package"
            })
            if existing_package:
                # Register in symbol table if not already there
                if package_qname not in self.symbol_table._qname_to_id:
                    self.symbol_table.add_symbol(
                        package_qname, existing_package.id
                    )
                return existing_package.id
        
        # Create the package node
        package_properties = PackageProperties(
            name=base_package,
            version="unknown"
        )
        
        created_package = PackageNode(
            name=base_package,
            qname=base_package,
            properties=package_properties
        )
        
        # Save to database
        saved_package = collections.nodes.create(created_package)
        
        # Store in our local mapping
        self.package_ids[package_qname] = saved_package.id
        
        # Create belongs_to edge linking package to project
        belongs_to_edge = BelongsToEdge(
            _from=saved_package.id,
            _to=self.project.id
        )
        collections.belongs_to_edges.create(belongs_to_edge)
        
        # Mark base package as created
        self.created_packages.add(base_package)
        
        # IMPORTANT: Register the package in the symbol table
        self.symbol_table.add_symbol(base_package, saved_package.id)
        # Also register the full qname if different from base
        if package_qname != base_package:
            self.symbol_table.add_symbol(package_qname, saved_package.id)
        
        return saved_package.id

    def _process_detail_pass_edges(self, edges: list) -> None:
        """
        Processes the edges from the detail pass, including dependency edges
        and call edges, creating package nodes as needed and linking them 
        properly.
        
        Args:
            edges: List of edge models (UsesImportEdge, CallEdge, etc.)
        """
        for edge in edges:
            if isinstance(edge, UsesImportEdge):
                self._process_import_edge(edge)
            elif isinstance(edge, CallEdge):
                self._process_call_edge(edge)

    def _process_import_edge(self, edge: UsesImportEdge) -> None:
        """
        Processes a single UsesImportEdge, creating package nodes as needed.
        
        Args:
            edge: The UsesImportEdge to process
        """
        target_qname = edge.target_qname
        if not target_qname:
            return
        
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

    def _process_call_edge(self, edge: CallEdge) -> None:
        """
        Processes a single CallEdge, ensuring both from_id and to_id 
        reference existing nodes.
        
        Args:
            edge: The CallEdge to process
        """
        # Verify that both nodes exist in the database
        from_node = collections.nodes.get(edge.from_id)
        to_node = collections.nodes.get(edge.to_id)
        
        if from_node and to_node:
            # Both nodes exist, create the edge
            collections.calls_edges.create(edge)
        else:
            # Log missing nodes for debugging
            if not from_node:
                print(f"Warning: Caller node {edge.from_id} not found")
            if not to_node:
                print(f"Warning: Target node {edge.to_id} not found")                

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
                    file_content = f.read()
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                continue

            # Get the file qname and find the corresponding file node
            file_qname = self.get_file_qname_from_path(file_path)
            file_node_id = self.symbol_table._qname_to_id.get(file_qname)
            
            if not file_node_id:
                print(f"Warning: Could not find file node for {file_path}")
                continue

            # Get hierarchical structure from file parser
            declared_nodes = self.file_parser.run_declaration_pass(
                file_path, file_content
            )
            
            # Also get the hierarchical visitor for structure information
            try:
                tree = ast.parse(file_content, filename=file_path)
            except SyntaxError as e:
                print(f"Syntax error in {file_path}: {e}")
                continue
                
            from app.core.parser.python.visitors.declaration_visitor import (
                DeclarationVisitor
            )
            visitor = DeclarationVisitor()
            visitor.visit(tree)
            
            # Create all nodes first and track them by qname
            created_nodes = {}  # qname -> created_node mapping
            hierarchical_nodes = {}  # qname -> hierarchical_node mapping
            
            # Build mapping of qnames to hierarchical nodes
            all_hierarchical_nodes = visitor.get_all_nodes_flat()
            for h_node in all_hierarchical_nodes:
                # Build qname based on hierarchy (same logic as in file_parser)
                qname_parts = []
                current = h_node
                while current:
                    if hasattr(current.ast_node, 'name'):
                        qname_parts.insert(0, current.ast_node.name)
                    current = current.parent
                
                file_qname_base = self.get_file_qname_from_path(file_path)
                if file_qname_base:
                    full_qname = f"{file_qname_base}.{'.'.join(qname_parts)}"
                else:
                    full_qname = '.'.join(qname_parts)
                
                hierarchical_nodes[full_qname] = h_node
            
            # Create all database nodes
            for node in declared_nodes:
                created_node = collections.nodes.create(node)
                self.symbol_table.add_symbol(
                    created_node.qname, created_node.id
                )
                created_nodes[created_node.qname] = created_node
                
                # Link declared nodes to project with BelongsToEdge
                belongs_to_edge = BelongsToEdge(
                    _from=created_node.id,
                    _to=self.project.id
                )
                collections.belongs_to_edges.create(belongs_to_edge)
            
            # Create ContainsEdge relationships based on actual hierarchy
            for node in declared_nodes:
                created_node = created_nodes[node.qname]
                hierarchical_node = hierarchical_nodes.get(node.qname)
                
                if hierarchical_node and hierarchical_node.parent:
                    # This node has a parent in the hierarchy
                    parent_h_node = hierarchical_node.parent
                    
                    # Build parent qname
                    parent_qname_parts = []
                    current = parent_h_node
                    while current:
                        if hasattr(current.ast_node, 'name'):
                            parent_qname_parts.insert(0, current.ast_node.name)
                        current = current.parent
                    
                    file_qname_base = self.get_file_qname_from_path(file_path)
                    if file_qname_base:
                        parent_qname = (
                            f"{file_qname_base}.{'.'.join(parent_qname_parts)}"
                        )
                    else:
                        parent_qname = '.'.join(parent_qname_parts)
                    
                    parent_created_node = created_nodes.get(parent_qname)
                    if parent_created_node:
                        # Create ContainsEdge from parent to child
                        contains_edge = ContainsEdge(
                            _from=parent_created_node.id,
                            _to=created_node.id,
                            position=node.properties.position
                        )
                        collections.contains_edges.create(contains_edge)
                    else:
                        # Parent not found, link to file
                        contains_edge = ContainsEdge(
                            _from=file_node_id,
                            _to=created_node.id,
                            position=node.properties.position
                        )
                        collections.contains_edges.create(contains_edge)
                else:
                    # Top-level node, link directly to file
                    contains_edge = ContainsEdge(
                        _from=file_node_id,
                        _to=created_node.id,
                        position=node.properties.position
                    )
                    collections.contains_edges.create(contains_edge)

        # Third Pass: Phase 2 - Process dependencies and imports
        # Now that all nodes are created and in the symbol table, we can
        
        for file_path in py_files:
            # Get the file qname and find the corresponding file node
            file_qname = self.get_file_qname_from_path(file_path)
            file_node_id = self.symbol_table._qname_to_id.get(file_qname)
            
            if not file_node_id:
                continue
                
            # Run the detail pass to get dependency and call edges
            detail_edges = self.file_parser.run_detail_pass(
                file_path, file_node_id
            )
            
            # Process the edges, creating package nodes as needed
            self._process_detail_pass_edges(detail_edges)

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
                len(self.file_parser.ast_cache._cache) 
                if hasattr(self.file_parser.ast_cache, '_cache') else 0
            )
        }
