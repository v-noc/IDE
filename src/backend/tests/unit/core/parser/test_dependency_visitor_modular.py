"""
Tests for the modular DependencyVisitor structure.

This test verifies that the refactored dependency visitor components
work together correctly after splitting the monolithic file.
"""

import ast
from app.core.parser.python.symbol_table import SymbolTable
from app.core.parser.python.visitors.detail_visitor.visitor_context import (
    VisitorContext
)
from app.core.parser.python.visitors.detail_visitor.dependency_visitor import (
    DependencyVisitor
)
from app.models.edges import UsesImportEdge


class TestModularDependencyVisitor:
    """Tests for the modular dependency visitor structure."""
    
    def test_modular_structure_components(self):
        """Test that all modular components are properly initialized."""
        # Setup
        symbol_table = SymbolTable()
        symbol_table.add_symbol("test_project.utils", "file_1")
        
        # Create context
        context = VisitorContext(
            file_id="file_test",
            ast_tree=ast.parse("import json"),
            symbol_table=symbol_table
        )
        
        # Create visitor
        visitor = DependencyVisitor(context)
        
        # Verify components are initialized
        assert hasattr(visitor, 'import_processor')
        assert hasattr(visitor, 'context_manager')
        assert hasattr(visitor, 'usage_detector')
        assert hasattr(visitor, 'context')
    
    def test_import_processing_delegation(self):
        """Test that import processing is properly delegated."""
        # Setup
        symbol_table = SymbolTable()
        code = "import json\nfrom typing import List"
        tree = ast.parse(code)
        
        context = VisitorContext(
            file_id="file_test",
            ast_tree=tree,
            symbol_table=symbol_table
        )
        
        visitor = DependencyVisitor(context)
        visitor.visit(tree)
        
        # Verify imports were processed
        processed_imports = visitor.import_processor.get_processed_imports()
        assert len(processed_imports) == 2
        assert isinstance(processed_imports[0], ast.Import)
        assert isinstance(processed_imports[1], ast.ImportFrom)
    
    def test_usage_detection_with_context(self):
        """Test that usage detection works with proper context."""
        # Setup
        symbol_table = SymbolTable()
        symbol_table.add_symbol("test_project", "project_1")
        symbol_table.add_symbol("test_project.main", "file_1")
        symbol_table.add_symbol("test_project.main.test_func", "func_1")
        
        code = '''
import json

def test_func():
    data = json.loads('{}')
    return data
'''
        
        tree = ast.parse(code)
        context = VisitorContext(
            file_id="file_1",
            ast_tree=tree,
            symbol_table=symbol_table
        )
        
        visitor = DependencyVisitor(context)
        visitor.visit(tree)
        
        # Check that usage edges were created
        usage_edges = [edge for edge in context.results 
                      if isinstance(edge, UsesImportEdge)]
        
        assert len(usage_edges) >= 1
        # Should have an edge for json.loads usage
        json_usage = [edge for edge in usage_edges 
                     if getattr(edge, 'target_qname', '') == 'json']
        assert len(json_usage) >= 1
    
    def test_analysis_summary(self):
        """Test the analysis summary functionality."""
        # Setup
        symbol_table = SymbolTable()
        code = '''
import json
from typing import List, Dict

def test_func():
    data = json.loads('{}')
    items: List[str] = []
    return data
'''
        
        tree = ast.parse(code)
        context = VisitorContext(
            file_id="file_test",
            ast_tree=tree,
            symbol_table=symbol_table
        )
        
        visitor = DependencyVisitor(context)
        visitor.visit(tree)
        
        # Get analysis summary
        summary = visitor.get_analysis_summary()
        
        assert "total_imports_processed" in summary
        assert "import_types" in summary
        assert "has_active_consumer" in summary
        assert "total_edges_created" in summary
        
        assert summary["total_imports_processed"] == 2
        assert summary["import_types"]["regular_imports"] == 1
        assert summary["import_types"]["from_imports"] == 1
    
    def test_component_isolation(self):
        """Test that components are properly isolated and can be tested independently."""
        # Setup
        symbol_table = SymbolTable()
        context = VisitorContext(
            file_id="file_test",
            ast_tree=ast.parse("import json"),
            symbol_table=symbol_table
        )
        
        visitor = DependencyVisitor(context)
        
        # Test import processor independently
        import_node = ast.parse("import numpy as np").body[0]
        visitor.import_processor.process_import(import_node)
        
        imports = visitor.import_processor.get_processed_imports()
        assert len(imports) == 1
        
        # Test context manager independently
        assert not visitor.context_manager.has_current_consumer()
        
        # Test that components maintain their state
        function_node = ast.parse("def test(): pass").body[0]
        # This should work without errors even if the function isn't in symbol table
        visitor.context_manager.visit_function_def(
            function_node, 
            lambda x: None  # No-op callback
        )
    
    def test_backwards_compatibility(self):
        """Test that the new modular structure maintains the same API."""
        # Setup - same as old tests would use
        symbol_table = SymbolTable()
        symbol_table.add_symbol("my_project.main", "file_1")
        symbol_table.add_symbol("my_project.main.func", "func_1")
        
        code = '''
import json
from fastapi import Request

def func():
    data = json.loads('{}')
    req = Request()
    return data, req
'''
        
        tree = ast.parse(code)
        context = VisitorContext(
            file_id="file_1",
            ast_tree=tree,
            symbol_table=symbol_table
        )
        
        # This should work exactly like the old DependencyVisitor
        visitor = DependencyVisitor(context)
        visitor.visit(tree)
        
        # Should produce the same results as before
        usage_edges = [edge for edge in context.results 
                      if isinstance(edge, UsesImportEdge)]
        
        assert len(usage_edges) >= 2  # json and Request usage
        
        # Verify edge properties are preserved
        for edge in usage_edges:
            assert hasattr(edge, 'target_qname')
            assert hasattr(edge, 'alias')
            assert hasattr(edge, 'target_symbol')
            assert hasattr(edge, 'import_position')
            assert hasattr(edge, 'usage_positions') 