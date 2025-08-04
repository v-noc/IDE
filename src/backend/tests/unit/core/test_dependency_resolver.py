"""
Tests for the DependencyResolver utility class.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.core.dependency_resolver import DependencyResolver
from app.core.code_elements import Function, Class
from app.core.package import Package
from app.models import node, edges


class TestDependencyResolver:
    """Test suite for DependencyResolver."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.resolver = DependencyResolver()
    
    @patch('app.core.dependency_resolver.db')
    def test_resolve_function_with_no_dependencies(self, mock_db):
        """Test resolving a function with no dependencies."""
        # Create mock function
        mock_function_node = Mock(spec=node.FunctionNode)
        mock_function_node.id = "func_1"
        mock_function_node.name = "test_function"
        mock_function_node.qname = "module.test_function"
        
        mock_function = Function(mock_function_node)
        mock_function.get_function_calls = Mock(return_value=[])
        mock_function.get_class_calls = Mock(return_value=[])
        mock_function.get_imports = Mock(return_value=[])
        
        # Resolve dependencies
        dependencies = self.resolver.resolve_dependencies(mock_function)
        
        # Should only contain the original function
        assert len(dependencies) == 1
        assert "func_1" in dependencies
        assert isinstance(dependencies["func_1"], Function)
    
    @patch('app.core.dependency_resolver.db')
    def test_resolve_function_with_function_calls(self, mock_db):
        """Test resolving a function that calls other functions."""
        # Create main function
        main_func_node = Mock(spec=node.FunctionNode)
        main_func_node.id = "main_func"
        main_func_node.name = "main_function"
        
        # Create called function
        called_func_node = Mock(spec=node.FunctionNode)
        called_func_node.id = "called_func"
        called_func_node.name = "called_function"
        
        main_function = Function(main_func_node)
        called_function = Function(called_func_node)
        
        # Mock function calls
        main_function.get_function_calls = Mock(return_value=[called_function])
        main_function.get_class_calls = Mock(return_value=[])
        main_function.get_imports = Mock(return_value=[])
        
        called_function.get_function_calls = Mock(return_value=[])
        called_function.get_class_calls = Mock(return_value=[])
        called_function.get_imports = Mock(return_value=[])
        
        # Resolve dependencies
        dependencies = self.resolver.resolve_dependencies(main_function)
        
        # Should contain both functions
        assert len(dependencies) == 2
        assert "main_func" in dependencies
        assert "called_func" in dependencies
    
    @patch('app.core.dependency_resolver.db')
    def test_resolve_function_with_class_dependency(self, mock_db):
        """Test resolving a function that uses a class."""
        # Create function
        func_node = Mock(spec=node.FunctionNode)
        func_node.id = "func_1"
        func_node.name = "get_user"
        
        # Create class
        class_node = Mock(spec=node.ClassNode)
        class_node.id = "class_1"
        class_node.name = "User"
        class_node.node_type = "class"
        
        function = Function(func_node)
        user_class = Class(class_node)
        
        # Mock class calls
        function.get_function_calls = Mock(return_value=[])
        function.get_class_calls = Mock(return_value=[user_class])
        function.get_imports = Mock(return_value=[])
        
        user_class.get_function_calls = Mock(return_value=[])
        user_class.get_class_calls = Mock(return_value=[])
        user_class.get_imports = Mock(return_value=[])
        user_class.methods = []
        
        # Resolve dependencies
        dependencies = self.resolver.resolve_dependencies(function)
        
        # Should contain function and class
        assert len(dependencies) == 2
        assert "func_1" in dependencies
        assert "class_1" in dependencies
        assert isinstance(dependencies["func_1"], Function)
        assert isinstance(dependencies["class_1"], Class)
    
    @patch('app.core.dependency_resolver.db')
    def test_resolve_function_with_import_dependencies(self, mock_db):
        """Test resolving a function with import dependencies."""
        # Create function
        func_node = Mock(spec=node.FunctionNode)
        func_node.id = "func_1"
        func_node.name = "test_function"
        
        # Create import edge to external package
        import_edge = Mock(spec=edges.UsesImportEdge)
        import_edge.to_id = "package_1"
        
        # Create package node
        package_node = Mock(spec=node.PackageNode)
        package_node.id = "package_1"
        package_node.name = "requests"
        package_node.node_type = "package"
        
        function = Function(func_node)
        function.get_function_calls = Mock(return_value=[])
        function.get_class_calls = Mock(return_value=[])
        function.get_imports = Mock(return_value=[import_edge])
        
        # Mock database calls
        mock_db.nodes.get.return_value = package_node
        
        # Resolve dependencies
        dependencies = self.resolver.resolve_dependencies(function)
        
        # Should contain function and package
        assert len(dependencies) == 2
        assert "func_1" in dependencies
        assert "package_1" in dependencies
        assert isinstance(dependencies["func_1"], Function)
        assert isinstance(dependencies["package_1"], Package)
    
    @patch('app.core.dependency_resolver.db')
    def test_resolve_circular_dependencies(self, mock_db):
        """Test that circular dependencies don't cause infinite loops."""
        # Create two functions that call each other
        func1_node = Mock(spec=node.FunctionNode)
        func1_node.id = "func_1"
        func1_node.name = "function_1"
        
        func2_node = Mock(spec=node.FunctionNode)
        func2_node.id = "func_2"
        func2_node.name = "function_2"
        
        function1 = Function(func1_node)
        function2 = Function(func2_node)
        
        # Create circular dependency
        function1.get_function_calls = Mock(return_value=[function2])
        function1.get_class_calls = Mock(return_value=[])
        function1.get_imports = Mock(return_value=[])
        
        function2.get_function_calls = Mock(return_value=[function1])
        function2.get_class_calls = Mock(return_value=[])
        function2.get_imports = Mock(return_value=[])
        
        # Resolve dependencies
        dependencies = self.resolver.resolve_dependencies(function1)
        
        # Should contain both functions, handled once each
        assert len(dependencies) == 2
        assert "func_1" in dependencies
        assert "func_2" in dependencies
    
    @patch('app.core.dependency_resolver.db')
    def test_get_dependency_summary(self, mock_db):
        """Test getting a dependency summary."""
        # Create function with various dependencies
        func_node = Mock(spec=node.FunctionNode)
        func_node.id = "main_func"
        func_node.name = "main_function"
        
        class_node = Mock(spec=node.ClassNode)
        class_node.id = "user_class"
        class_node.name = "User"
        
        package_node = Mock(spec=node.PackageNode)
        package_node.id = "requests_pkg"
        package_node.name = "requests"
        package_node.qname = "requests"
        package_node.node_type = "package"
        
        function = Function(func_node)
        user_class = Class(class_node)
        
        # Mock dependencies
        function.get_function_calls = Mock(return_value=[])
        function.get_class_calls = Mock(return_value=[user_class])
        function.get_imports = Mock(return_value=[])
        
        user_class.get_function_calls = Mock(return_value=[])
        user_class.get_class_calls = Mock(return_value=[])
        user_class.methods = []
        
        # Mock import edge
        import_edge = Mock(spec=edges.UsesImportEdge)
        import_edge.to_id = "requests_pkg"
        user_class.get_imports = Mock(return_value=[import_edge])
        
        mock_db.nodes.get.return_value = package_node
        
        # Get summary
        summary = self.resolver.get_dependency_summary(function)
        
        # Verify summary structure
        assert 'functions' in summary
        assert 'classes' in summary
        assert 'packages' in summary
        assert 'total_count' in summary
        
        # Should have 1 class and 1 package dependency (excluding main function)
        assert len(summary['classes']) == 1
        assert len(summary['packages']) == 1
        assert summary['classes'][0]['name'] == 'User'
        assert summary['packages'][0]['name'] == 'requests'
    
    def test_empty_resolver_initialization(self):
        """Test that resolver initializes with empty state."""
        resolver = DependencyResolver()
        assert len(resolver.visited_nodes) == 0
        assert len(resolver.resolved_dependencies) == 0
    
    def test_resolver_state_clears_between_calls(self):
        """Test that resolver state is cleared between dependency resolution calls."""
        # Mock a simple function
        func_node = Mock(spec=node.FunctionNode)
        func_node.id = "func_1"
        func_node.name = "test_function"
        
        function = Function(func_node)
        function.get_function_calls = Mock(return_value=[])
        function.get_class_calls = Mock(return_value=[])
        function.get_imports = Mock(return_value=[])
        
        # First resolution
        dependencies1 = self.resolver.resolve_dependencies(function)
        assert len(dependencies1) == 1
        
        # Second resolution should work independently
        dependencies2 = self.resolver.resolve_dependencies(function)
        assert len(dependencies2) == 1
        assert dependencies1 == dependencies2 