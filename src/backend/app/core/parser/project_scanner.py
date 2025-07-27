# src/backend/app/core/parser/project_scanner.py
import os
from typing import Dict, Any

from app.db import collections
from app.models.edges import (
    BelongsToEdge, ContainsEdge, UsesImportEdge, CallEdge
)
from app.models import edges
from app.models.node import PackageNode
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
        Creates a package node for an external package if it doesn't exist.
        Only creates one node per base package and tracks imported paths.
        
        Args:
            package_qname: The fully qualified name of the package
            
        Returns:
            The database ID of the created package node
        """
        # Extract base package name (e.g., "pydantic" from 
        # "pydantic.BaseModel")
        base_package = package_qname.split('.')[0]
        
        # Check if base package already exists
        if base_package in self.created_packages:
      
            existing_package_id = self.package_ids.get(base_package)
            if existing_package_id:
                # Update the existing package with new imported path
                existing_node = collections.nodes.get(existing_package_id)
                if (existing_node and package_qname not in 
                        existing_node.properties.imported_paths):
                    existing_node.properties.imported_paths.append(
                        package_qname
                    )
                    collections.nodes.update(existing_node)
                return existing_package_id
        
        # Create the package node
        package_node = PackageNode(
            name=base_package,  # Use base package as name
            qname=base_package,  # Use base package as qname
            properties=PackageProperties(imported_paths=[package_qname])
        )
        
        # Save to database
        created_package = collections.nodes.create(package_node)
        
        # Track the package ID for future lookups
        self.package_ids[base_package] = created_package.id
        
        # Link package to project with BelongsToEdge
        belongs_to_edge = BelongsToEdge(
            _from=created_package.id,
            _to=self.project.id
        )
        collections.belongs_to_edges.create(belongs_to_edge)
        
        # Mark base package as created
        self.created_packages.add(base_package)
        
        return created_package.id

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
            
            # Create nodes and track class-method relationships
            class_nodes = {}  # qname -> node_id mapping for classes
            method_parent_mapping = {}  # method_node_id -> class_node_id
            
            for node in declared_nodes:
                created_node = collections.nodes.create(node)
                self.symbol_table.add_symbol(
                    created_node.qname, created_node.id
                )
                
                # Track class nodes for method linking
                if created_node.node_type == 'class':
                    class_nodes[created_node.qname] = created_node.id
                elif created_node.node_type == 'function':
                    # Check if this is a method (has parent class in qname)
                    qname_parts = created_node.qname.split('.')
                    if len(qname_parts) >= 2:
                        # Try to find parent class by removing last part of qname
                        potential_class_qname = '.'.join(qname_parts[:-1])
                        if potential_class_qname in class_nodes:
                            method_parent_mapping[created_node.id] = (
                                class_nodes[potential_class_qname]
                            )
                
                # Link declared nodes to their file with ContainsEdge
                contains_edge = ContainsEdge(
                    _from=file_node_id,
                    _to=created_node.id,
                    position=node.properties.position
                )
                collections.contains_edges.create(contains_edge)
                
                # Link declared nodes to project with BelongsToEdge
                # Not Sure the usage of this edge (might be removed)
                belongs_to_edge = BelongsToEdge(
                    _from=created_node.id,
                    _to=self.project.id
                )
                collections.belongs_to_edges.create(belongs_to_edge)
            
            # Create implements edges for method-class relationships
            for method_id, class_id in method_parent_mapping.items():
                implements_edge = edges.ImplementsEdge(
                    _from=class_id,
                    _to=method_id
                )
                collections.implements_edges.create(implements_edge)
                
                
        # Third Pass: Phase 2 - Process dependencies and imports
        
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
