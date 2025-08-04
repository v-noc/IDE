"""
Tests for VirtualFile code element and dependency functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.core.virtual_file import VirtualFile
from app.core.code_elements import Function, Class
from app.core.package import Package
from app.core.dependency_resolver import DependencyResolver
from app.models import node, edges


class TestVirtualFileDependencies:
    """Test suite for VirtualFile dependency functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Create a mock virtual file node
        self.virtual_file_node = Mock(spec=node.VirtualFileNode)
        self.virtual_file_node.key = "vfile_1"
        self.virtual_file_node.id = "vfile_1"
        self.virtual_file_node.name = "test_virtual_file"
        self.virtual_file_node.qname = "project.test_virtual_file"
        self.virtual_file_node.description = "Test virtual file"
        self.virtual_file_node.node_type = "virtual_file"
        
        self.virtual_file = VirtualFile(self.virtual_file_node)
    
    @patch('app.core.virtual_file.db')
    @patch('app.core.virtual_file.DependencyResolver')
    def test_add_single_function_without_dependencies(self, mock_resolver_class, mock_db):
        """Test adding a single function without its dependencies."""
        # Create mock function
        func_node = Mock(spec=node.FunctionNode)
        func_node.id = "func_1"
        func_node.name = "test_function"
        func_node.qname = "module.test_function"
        
        function = Function(func_node)
        
        # Mock database operations
        mock_db.virtual_contains_edges.find_one.return_value = None
        mock_db.virtual_contains_edges.create.return_value = None
        
        # Add function without dependencies
        result = self.virtual_file.add_code_element_with_dependencies(
            element=function,
            include_dependencies=False
        )
        
        # Verify results
        assert result['total_count'] == 1
        assert len(result['functions']) == 1
        assert result['functions'][0]['id'] == 'func_1'
        assert result['functions'][0]['name'] == 'test_function'
        assert len(result['classes']) == 0
        assert len(result['packages']) == 0
        
        # Verify virtual contains edge was created
        mock_db.virtual_contains_edges.create.assert_called_once()
    
    @patch('app.core.virtual_file.db')
    @patch('app.core.virtual_file.DependencyResolver')
    def test_add_function_with_dependencies(self, mock_resolver_class, mock_db):
        """Test adding a function with its dependencies."""
        # Create mock function and its dependencies
        func_node = Mock(spec=node.FunctionNode)
        func_node.id = "func_1"
        func_node.name = "get_user"
        func_node.qname = "module.get_user"
        
        class_node = Mock(spec=node.ClassNode)
        class_node.id = "class_1"
        class_node.name = "User"
        class_node.qname = "module.User"
        
        function = Function(func_node)
        user_class = Class(class_node)
        
        # Mock resolver
        mock_resolver = Mock(spec=DependencyResolver)
        mock_resolver.resolve_dependencies.return_value = {
            "func_1": function,
            "class_1": user_class
        }
        mock_resolver_class.return_value = mock_resolver
        
        # Mock database operations
        mock_db.virtual_contains_edges.find_one.return_value = None
        mock_db.virtual_contains_edges.create.return_value = None
        
        # Add function with dependencies
        result = self.virtual_file.add_code_element_with_dependencies(
            element=function,
            include_dependencies=True
        )
        
        # Verify results
        assert result['total_count'] == 2
        assert len(result['functions']) == 1
        assert len(result['classes']) == 1
        assert result['functions'][0]['name'] == 'get_user'
        assert result['classes'][0]['name'] == 'User'
        
        # Verify resolver was called
        mock_resolver.resolve_dependencies.assert_called_once_with(function)
        
        # Verify virtual contains edges were created for both elements
        assert mock_db.virtual_contains_edges.create.call_count == 2
    
    @patch('app.core.virtual_file.db')
    @patch('app.core.virtual_file.DependencyResolver')
    def test_add_function_with_package_dependencies(self, mock_resolver_class, mock_db):
        """Test adding a function that depends on external packages."""
        # Create mock function and package
        func_node = Mock(spec=node.FunctionNode)
        func_node.id = "func_1"
        func_node.name = "make_request"
        func_node.qname = "module.make_request"
        
        package_node = Mock(spec=node.PackageNode)
        package_node.id = "pkg_1"
        package_node.name = "requests"
        package_node.qname = "requests"
        
        function = Function(func_node)
        requests_package = Package(package_node)
        
        # Mock resolver
        mock_resolver = Mock(spec=DependencyResolver)
        mock_resolver.resolve_dependencies.return_value = {
            "func_1": function,
            "pkg_1": requests_package
        }
        mock_resolver_class.return_value = mock_resolver
        
        # Mock database operations
        mock_db.virtual_contains_edges.find_one.return_value = None
        mock_db.virtual_contains_edges.create.return_value = None
        
        # Add function with dependencies
        result = self.virtual_file.add_code_element_with_dependencies(
            element=function,
            include_dependencies=True
        )
        
        # Verify results
        assert result['total_count'] == 2
        assert len(result['functions']) == 1
        assert len(result['packages']) == 1
        assert result['functions'][0]['name'] == 'make_request'
        assert result['packages'][0]['name'] == 'requests'
    
    @patch('app.core.virtual_file.db')
    def test_add_already_existing_element(self, mock_db):
        """Test adding an element that already exists in the virtual file."""
        # Create mock function
        func_node = Mock(spec=node.FunctionNode)
        func_node.id = "func_1"
        func_node.name = "test_function"
        
        function = Function(func_node)
        
        # Mock existing edge
        existing_edge = Mock()
        mock_db.virtual_contains_edges.find_one.return_value = existing_edge
        
        # Add function
        result = self.virtual_file.add_code_element_with_dependencies(
            element=function,
            include_dependencies=False
        )
        
        # Should skip creation and return empty result
        assert result['total_count'] == 0
        assert len(result['functions']) == 0
        
        # Verify no new edge was created
        mock_db.virtual_contains_edges.create.assert_not_called()
    
    @patch('app.core.virtual_file.db')
    def test_remove_code_element_success(self, mock_db):
        """Test successfully removing a code element."""
        # Mock existing edge
        existing_edge = Mock()
        existing_edge.key = "edge_1"
        mock_db.virtual_contains_edges.find_one.return_value = existing_edge
        mock_db.virtual_contains_edges.delete.return_value = None
        
        # Remove element
        result = self.virtual_file.remove_code_element("func_1")
        
        # Verify success
        assert result is True
        mock_db.virtual_contains_edges.find_one.assert_called_once_with({
            'from_id': self.virtual_file.id,
            'to_id': 'func_1'
        })
        mock_db.virtual_contains_edges.delete.assert_called_once_with("edge_1")
    
    @patch('app.core.virtual_file.db')
    def test_remove_code_element_not_found(self, mock_db):
        """Test removing a code element that doesn't exist."""
        # Mock no existing edge
        mock_db.virtual_contains_edges.find_one.return_value = None
        
        # Remove element
        result = self.virtual_file.remove_code_element("func_1")
        
        # Verify failure
        assert result is False
        mock_db.virtual_contains_edges.delete.assert_not_called()
    
    @patch('app.core.virtual_file.db')
    def test_get_code_elements_summary(self, mock_db):
        """Test getting a summary of all code elements in the virtual file."""
        # Mock database calls for different element types
        func_node = Mock(spec=node.FunctionNode)
        func_node.id = "func_1"
        func_node.name = "test_function"
        func_node.qname = "module.test_function"
        
        class_node = Mock(spec=node.ClassNode)
        class_node.id = "class_1"
        class_node.name = "TestClass"
        class_node.qname = "module.TestClass"
        
        package_node = Mock(spec=node.PackageNode)
        package_node.id = "pkg_1"
        package_node.name = "requests"
        package_node.qname = "requests"
        
        # Mock find_related calls
        mock_db.nodes.find_related.side_effect = [
            [func_node],  # functions
            [class_node],  # classes
            [package_node]  # packages
        ]
        
        # Get summary
        summary = self.virtual_file.get_code_elements_summary()
        
        # Verify summary
        assert summary['total_count'] == 3
        assert len(summary['functions']) == 1
        assert len(summary['classes']) == 1
        assert len(summary['packages']) == 1
        
        assert summary['functions'][0]['name'] == 'test_function'
        assert summary['classes'][0]['name'] == 'TestClass'
        assert summary['packages'][0]['name'] == 'requests'
    
    @patch('app.core.virtual_file.db')
    def test_get_functions(self, mock_db):
        """Test getting all functions in the virtual file."""
        # Mock function node
        func_node = Mock(spec=node.FunctionNode)
        func_node.id = "func_1"
        func_node.name = "test_function"
        
        mock_db.nodes.find_related.return_value = [func_node]
        
        # Get functions
        functions = self.virtual_file.get_functions()
        
        # Verify results
        assert len(functions) == 1
        assert isinstance(functions[0], Function)
        assert functions[0].model == func_node
        
        # Verify correct database call
        mock_db.nodes.find_related.assert_called_once_with(
            start_node_id=self.virtual_file.id,
            edge_collection=mock_db.virtual_contains_edges,
            direction="outbound",
            filter_by_type="function"
        )
    
    @patch('app.core.virtual_file.db')
    def test_get_classes(self, mock_db):
        """Test getting all classes in the virtual file."""
        # Mock class node
        class_node = Mock(spec=node.ClassNode)
        class_node.id = "class_1"
        class_node.name = "TestClass"
        
        mock_db.nodes.find_related.return_value = [class_node]
        
        # Get classes
        classes = self.virtual_file.get_classes()
        
        # Verify results
        assert len(classes) == 1
        assert isinstance(classes[0], Class)
        assert classes[0].model == class_node
        
        # Verify correct database call
        mock_db.nodes.find_related.assert_called_once_with(
            start_node_id=self.virtual_file.id,
            edge_collection=mock_db.virtual_contains_edges,
            direction="outbound",
            filter_by_type="class"
        )
    
    @patch('app.core.virtual_file.db')
    def test_get_packages(self, mock_db):
        """Test getting all packages in the virtual file."""
        # Mock package node
        package_node = Mock(spec=node.PackageNode)
        package_node.id = "pkg_1"
        package_node.name = "requests"
        
        mock_db.nodes.find_related.return_value = [package_node]
        
        # Get packages
        packages = self.virtual_file.get_packages()
        
        # Verify results
        assert len(packages) == 1
        assert isinstance(packages[0], Package)
        assert packages[0].model == package_node
        
        # Verify correct database call
        mock_db.nodes.find_related.assert_called_once_with(
            start_node_id=self.virtual_file.id,
            edge_collection=mock_db.virtual_contains_edges,
            direction="outbound",
            filter_by_type="package"
        ) 