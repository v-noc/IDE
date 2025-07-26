"""
Integration tests for Phase 2: Dependency and Import Resolution

These tests verify that the complete Phase 2 pipeline works correctly,
from parsing imports to creating dependency edges and package nodes.
"""

import tempfile
import os
from app.core.parser.python.symbol_table import SymbolTable
from app.core.parser.python.file_parser import PythonFileParser
from app.core.parser.python.ast_cache import ASTCache
from app.models.edges import UsesImportEdge


class TestPhase2Integration:
    """Integration tests for Phase 2 dependency resolution."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        self.ast_cache = ASTCache()
        self.symbol_table = SymbolTable()
        self.project_root = "/fake/project"
        self.file_parser = PythonFileParser(
            self.ast_cache, self.symbol_table, self.project_root
        )
        
        # Set up some mock symbols
        self.symbol_table.add_symbol("my_project", "project_1")
        self.symbol_table.add_symbol("my_project.utils", "file_2")
        self.symbol_table.add_symbol("my_project.models", "file_3")
        self.symbol_table.add_symbol("my_project.main.main_func", "func_1")

    def test_simple_import_resolution(self):
        """Test resolution of simple import statements."""
        # Sample Python code with imports
        test_code = '''
import json
import os
from fastapi import Request
from my_project.utils import helper_func

def main_func():
    data = json.loads('{}')
    path = os.path.join('a', 'b')
    request = Request()
    result = helper_func()
    return result
'''
        
        # Mock file operations
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            f.flush()
            
            try:
                # Run declaration pass first
                declared_nodes = self.file_parser.run_declaration_pass(
                    f.name, test_code
                )
                # Verify function was declared
                assert len(declared_nodes) == 1
                func_node = declared_nodes[0]
                assert func_node.name == "main_func"
                
                # Add the function to symbol table
                self.symbol_table.add_symbol(func_node.qname, "func_main_id")
                
                # Add the file to symbol table so context manager can find it
                file_qname = f.name.replace(self.project_root, "").lstrip("/").replace(".py", "").replace("/", ".")
                self.symbol_table.add_symbol(file_qname, "file_main")
                
                # Debug: Check if function is in symbol table
               
                
                # Run detail pass
                dependency_edges = self.file_parser.run_detail_pass(
                    f.name, "file_main"
                )
                
               
                # Verify import edges were created
                usage_edges = [
                    edge for edge in dependency_edges 
                    if isinstance(edge, UsesImportEdge)
                ]
                
                # Should have edges for json, os, Request, and helper_func usage
                assert len(usage_edges) >= 4
                
                # Verify target qnames are correct
                target_qnames = [
                    getattr(edge, 'target_qname', '') for edge in usage_edges
                ]
                
                assert 'json' in target_qnames
                assert 'os' in target_qnames  
                assert 'fastapi.Request' in target_qnames
                assert 'my_project.utils.helper_func' in target_qnames
                
            finally:
                os.unlink(f.name)

    def test_aliased_import_resolution(self):
        """Test resolution of aliased imports."""
        test_code = '''
import numpy as np
from typing import List as ListType
from my_project.utils import helper as h

def process_data():
    arr = np.array([1, 2, 3])
    items: ListType[int] = [1, 2, 3]
    result = h.process(items)
    return result
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            f.flush()
            
            try:
                # Run both passes
                declared_nodes = self.file_parser.run_declaration_pass(
                    f.name, test_code
                )
                
                # Add function to symbol table
                func_node = declared_nodes[0]
                self.symbol_table.add_symbol(func_node.qname, "func_process")
                
                # Add the file to symbol table so context manager can find it
                file_qname = f.name.replace(self.project_root, "").lstrip("/").replace(".py", "").replace("/", ".")
                self.symbol_table.add_symbol(file_qname, "file_process")

                dependency_edges = self.file_parser.run_detail_pass(
                    f.name, "file_process"
                )
                
                usage_edges = [
                    edge for edge in dependency_edges 
                    if isinstance(edge, UsesImportEdge)
                ]
                
                # Should have edges for aliased imports
                assert len(usage_edges) >= 3
                
                # Check aliases are preserved
                aliases = [edge.alias for edge in usage_edges]
                assert 'np' in aliases
                assert 'ListType' in aliases
                assert 'h' in aliases
                
            finally:
                os.unlink(f.name)

    def test_local_vs_external_detection(self):
        """Test that local modules and external packages are distinguished."""
        # Add some local modules
        self.symbol_table.add_symbol("my_project.auth", "file_auth")
        self.symbol_table.add_symbol("my_project.db.models", "file_models")
        
        # Test local module detection
        assert self.symbol_table.is_local_module("my_project.utils") is True
        assert self.symbol_table.is_local_module("my_project.auth.login") is True
        assert self.symbol_table.is_local_module("my_project.db.models.User") is True
        
        # Test external package detection
        assert self.symbol_table.is_local_module("fastapi") is False
        assert self.symbol_table.is_local_module("numpy") is False
        assert self.symbol_table.is_local_module("requests.get") is False

    def test_relative_imports(self):
        """Test resolution of relative imports."""
        test_code = '''
from . import sibling_module
from ..utils import parent_utility
from ...common import shared_function

def use_relatives():
    sibling_module.do_something()
    parent_utility.help()
    shared_function.process()
'''
        
        # Set up file context for relative imports
        file_path = "/fake/project/subdir/module.py"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            f.flush()
            
            try:
                declared_nodes = self.file_parser.run_declaration_pass(
                    file_path, test_code
                )
                
                func_node = declared_nodes[0]
                self.symbol_table.add_symbol(func_node.qname, "func_relatives")
                
                # Add the file to symbol table so context manager can find it
                file_qname = file_path.replace(self.project_root, "").lstrip("/").replace(".py", "").replace("/", ".")
                self.symbol_table.add_symbol(file_qname, "file_relatives")

                dependency_edges = self.file_parser.run_detail_pass(
                    file_path, "file_relatives"
                )
                
                usage_edges = [
                    edge for edge in dependency_edges 
                    if isinstance(edge, UsesImportEdge)
                ]
                
                # Should handle relative imports
                assert len(usage_edges) >= 3
                
            finally:
                os.unlink(f.name)

    def test_complex_attribute_chains(self):
        """Test resolution of complex attribute access chains."""
        test_code = '''
import requests
from my_project.auth import session_manager

def make_request():
    response = requests.get('http://example.com')
    data = response.json()
    
    auth = session_manager.get_current_session()
    token = auth.user.token
    
    return data, token
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            f.flush()
            
            try:
                declared_nodes = self.file_parser.run_declaration_pass(
                    f.name, test_code
                )
                
                func_node = declared_nodes[0]
                self.symbol_table.add_symbol(func_node.qname, "func_request")
                
                # Add the file to symbol table so context manager can find it
                file_qname = f.name.replace(self.project_root, "").lstrip("/").replace(".py", "").replace("/", ".")
                self.symbol_table.add_symbol(file_qname, "file_request")

                dependency_edges = self.file_parser.run_detail_pass(
                    f.name, "file_request"
                )
                
                usage_edges = [
                    edge for edge in dependency_edges 
                    if isinstance(edge, UsesImportEdge)
                ]
                
                # Should capture various usage patterns
                assert len(usage_edges) >= 2
                
                # Check that both direct usage and attribute access are captured
                target_symbols = [edge.target_symbol for edge in usage_edges]
                assert any('get' in symbol for symbol in target_symbols)
                assert any('session_manager' in symbol for symbol in target_symbols)
                
            finally:
                os.unlink(f.name)

    def test_edge_case_handling(self):
        """Test handling of edge cases and malformed imports."""
        test_code = '''
# Various edge cases
from . import *  # Star import
try:
    import nonexistent_package
except ImportError:
    pass

def edge_case_func():
    # This should not break the parser
    if True:
        import conditional_import
        conditional_import.do_something()
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            f.flush()
            
            try:
                # Should not raise exceptions
                declared_nodes = self.file_parser.run_declaration_pass(
                    f.name, test_code
                )
                
                func_node = declared_nodes[0]
                self.symbol_table.add_symbol(func_node.qname, "func_edge")
                
                dependency_edges = self.file_parser.run_detail_pass(
                    f.name, "file_edge"
                )
                
                # Should handle gracefully without crashing
                assert isinstance(dependency_edges, list)
                
            finally:
                os.unlink(f.name)

    def test_import_position_tracking(self):
        """Test that import positions are correctly tracked."""
        test_code = '''
import json  # Line 2
from fastapi import Request  # Line 3

def func():  # Line 5
    data = json.loads('{}')  # Usage at line 6
    req = Request()  # Usage at line 7
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            f.flush()
            
            try:
                declared_nodes = self.file_parser.run_declaration_pass(
                    f.name, test_code
                )
                
                func_node = declared_nodes[0]
                self.symbol_table.add_symbol(func_node.qname, "func_pos")
                
                dependency_edges = self.file_parser.run_detail_pass(
                    f.name, "file_pos"
                )
                
                usage_edges = [
                    edge for edge in dependency_edges 
                    if isinstance(edge, UsesImportEdge)
                ]
                
                # Verify position information is captured
                for edge in usage_edges:
                    assert hasattr(edge, 'import_position')
                    assert hasattr(edge, 'usage_positions')
                    assert edge.import_position.line_no > 0
                    assert len(edge.usage_positions) > 0
                    assert all(pos.line_no > 0 for pos in edge.usage_positions)
                
            finally:
                os.unlink(f.name) 