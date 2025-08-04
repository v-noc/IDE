"""
Tests for VirtualFolder code element and dependency functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.core.virtual_folder import VirtualFolder
from app.core.virtual_file import VirtualFile
from app.core.code_elements import Function, Class
from app.models import node


class TestVirtualFolderDependencies:
    """Test suite for VirtualFolder dependency functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Create a mock virtual folder node
        self.virtual_folder_node = Mock(spec=node.VirtualFolderNode)
        self.virtual_folder_node.key = "vfolder_1"
        self.virtual_folder_node.id = "vfolder_1"
        self.virtual_folder_node.name = "test_virtual_folder"
        self.virtual_folder_node.qname = "project.test_virtual_folder"
        self.virtual_folder_node.description = "Test virtual folder"
        self.virtual_folder_node.node_type = "virtual_folder"
        
        self.virtual_folder = VirtualFolder(self.virtual_folder_node)
    
    @patch('app.core.virtual_folder.db')
    def test_add_code_element_creates_new_virtual_file(self, mock_db):
        """Test adding a code element creates a new virtual file when none specified."""
        # Create mock function
        func_node = Mock(spec=node.FunctionNode)
        func_node.id = "func_1"
        func_node.name = "get_user"
        func_node.qname = "module.get_user"
        
        function = Function(func_node)
        
        # Mock virtual file creation
        mock_virtual_file_node = Mock(spec=node.VirtualFileNode)
        mock_virtual_file_node.id = "vfile_1"
        mock_virtual_file_node.name = "get_user_virtual_file"
        mock_virtual_file_node.qname = "project.test_virtual_folder.get_user_virtual_file"
        
        mock_db.nodes.create.return_value = mock_virtual_file_node
        mock_db.virtual_contains_edges.create.return_value = None
        
        # Mock the virtual file's add_code_element_with_dependencies method
        with patch('app.core.virtual_folder.VirtualFile') as mock_vfile_class:
            mock_virtual_file = Mock(spec=VirtualFile)
            mock_virtual_file.id = "vfile_1"
            mock_virtual_file.name = "get_user_virtual_file"
            mock_virtual_file.qname = "project.test_virtual_folder.get_user_virtual_file"
            mock_virtual_file.add_code_element_with_dependencies.return_value = {
                'functions': [{'id': 'func_1', 'name': 'get_user', 'qname': 'module.get_user'}],
                'classes': [],
                'packages': [],
                'total_count': 1
            }
            mock_vfile_class.return_value = mock_virtual_file
            
            # Add code element
            result = self.virtual_folder.add_code_element_with_dependencies(
                element=function,
                include_dependencies=True
            )
        
        # Verify results
        assert 'virtual_file' in result
        assert result['virtual_file']['name'] == 'get_user_virtual_file'
        assert result['total_count'] == 1
        assert len(result['functions']) == 1
        assert result['functions'][0]['name'] == 'get_user'
    
    @patch('app.core.virtual_folder.VirtualFile')
    def test_add_code_element_to_existing_virtual_file(self, mock_vfile_class):
        """Test adding a code element to an existing virtual file."""
        # Create mock function
        func_node = Mock(spec=node.FunctionNode)
        func_node.id = "func_1"
        func_node.name = "process_data"
        
        function = Function(func_node)
        
        # Create mock target virtual file
        mock_target_file = Mock(spec=VirtualFile)
        mock_target_file.id = "existing_vfile"
        mock_target_file.name = "existing_file"
        mock_target_file.qname = "project.test_virtual_folder.existing_file"
        mock_target_file.add_code_element_with_dependencies.return_value = {
            'functions': [{'id': 'func_1', 'name': 'process_data', 'qname': 'module.process_data'}],
            'classes': [],
            'packages': [],
            'total_count': 1
        }
        
        # Add code element to existing file
        result = self.virtual_folder.add_code_element_with_dependencies(
            element=function,
            target_virtual_file=mock_target_file,
            include_dependencies=False
        )
        
        # Verify results
        assert 'virtual_file' in result
        assert result['virtual_file']['name'] == 'existing_file'
        assert result['total_count'] == 1
        
        # Verify the existing file's method was called
        mock_target_file.add_code_element_with_dependencies.assert_called_once_with(
            element=function,
            include_dependencies=False
        )
    
    @patch('app.core.virtual_folder.db')
    def test_add_multiple_code_elements_to_separate_files(self, mock_db):
        """Test adding multiple code elements to separate virtual files."""
        # Create mock functions
        func1_node = Mock(spec=node.FunctionNode)
        func1_node.id = "func_1"
        func1_node.name = "get_user"
        
        func2_node = Mock(spec=node.FunctionNode)
        func2_node.id = "func_2"
        func2_node.name = "save_user"
        
        class1_node = Mock(spec=node.ClassNode)
        class1_node.id = "class_1"
        class1_node.name = "UserService"
        
        function1 = Function(func1_node)
        function2 = Function(func2_node)
        user_service = Class(class1_node)
        
        elements = [function1, function2, user_service]
        
        # Mock virtual file creation for each element
        mock_vfile_nodes = []
        for i, element in enumerate(elements):
            mock_node = Mock(spec=node.VirtualFileNode)
            mock_node.id = f"vfile_{i+1}"
            mock_node.name = f"{element.name}_module"
            mock_node.qname = f"project.test_virtual_folder.{element.name}_module"
            mock_vfile_nodes.append(mock_node)
        
        mock_db.nodes.create.side_effect = mock_vfile_nodes
        mock_db.virtual_contains_edges.create.return_value = None
        
        # Mock VirtualFile instances
        with patch('app.core.virtual_folder.VirtualFile') as mock_vfile_class:
            mock_virtual_files = []
            for i, element in enumerate(elements):
                mock_vfile = Mock(spec=VirtualFile)
                mock_vfile.id = f"vfile_{i+1}"
                mock_vfile.name = f"{element.name}_module"
                mock_vfile.qname = f"project.test_virtual_folder.{element.name}_module"
                
                # Mock the add_code_element_with_dependencies response
                element_type = 'functions' if isinstance(element, Function) else 'classes'
                mock_vfile.add_code_element_with_dependencies.return_value = {
                    'functions': [{'id': element.id, 'name': element.name, 'qname': f'module.{element.name}'}] if element_type == 'functions' else [],
                    'classes': [{'id': element.id, 'name': element.name, 'qname': f'module.{element.name}'}] if element_type == 'classes' else [],
                    'packages': [],
                    'total_count': 1
                }
                mock_virtual_files.append(mock_vfile)
            
            mock_vfile_class.side_effect = mock_virtual_files
            
            # Add multiple elements
            result = self.virtual_folder.add_code_elements_to_separate_files(
                elements=elements,
                include_dependencies=False
            )
        
        # Verify results
        assert len(result['virtual_files_created']) == 3
        assert result['total_elements_added'] == 3
        assert len(result['elements_by_file']) == 3
        
        # Check that each element got its own file
        file_names = [vf['name'] for vf in result['virtual_files_created']]
        assert 'get_user_module' in file_names
        assert 'save_user_module' in file_names
        assert 'UserService_module' in file_names
    
    @patch('app.core.virtual_folder.VirtualFile')
    def test_get_all_code_elements_summary(self, mock_vfile_class):
        """Test getting a summary of all code elements across virtual files."""
        # Create mock virtual files
        mock_vfile1 = Mock(spec=VirtualFile)
        mock_vfile1.id = "vfile_1"
        mock_vfile1.name = "file1"
        mock_vfile1.qname = "project.test_virtual_folder.file1"
        mock_vfile1.get_code_elements_summary.return_value = {
            'functions': [{'id': 'func_1', 'name': 'function1', 'qname': 'module.function1'}],
            'classes': [],
            'packages': [],
            'total_count': 1
        }
        
        mock_vfile2 = Mock(spec=VirtualFile)
        mock_vfile2.id = "vfile_2"
        mock_vfile2.name = "file2"
        mock_vfile2.qname = "project.test_virtual_folder.file2"
        mock_vfile2.get_code_elements_summary.return_value = {
            'functions': [],
            'classes': [{'id': 'class_1', 'name': 'Class1', 'qname': 'module.Class1'}],
            'packages': [{'id': 'pkg_1', 'name': 'requests', 'qname': 'requests'}],
            'total_count': 2
        }
        
        # Mock get_virtual_files
        with patch.object(self.virtual_folder, 'get_virtual_files', return_value=[mock_vfile1, mock_vfile2]):
            summary = self.virtual_folder.get_all_code_elements_summary()
        
        # Verify aggregated summary
        assert summary['virtual_files_count'] == 2
        assert summary['aggregated']['total_count'] == 3
        assert len(summary['aggregated']['functions']) == 1
        assert len(summary['aggregated']['classes']) == 1
        assert len(summary['aggregated']['packages']) == 1
        
        # Verify by-file breakdown
        assert len(summary['by_file']) == 2
        assert summary['by_file'][0]['file_name'] == 'file1'
        assert summary['by_file'][1]['file_name'] == 'file2'
    
    @patch('app.core.virtual_folder.db')
    def test_get_virtual_files(self, mock_db):
        """Test getting all virtual files in the folder."""
        # Mock virtual file nodes
        vfile1_node = Mock(spec=node.VirtualFileNode)
        vfile1_node.id = "vfile_1"
        vfile1_node.name = "file1"
        
        vfile2_node = Mock(spec=node.VirtualFileNode)
        vfile2_node.id = "vfile_2"
        vfile2_node.name = "file2"
        
        mock_db.nodes.find_related.return_value = [vfile1_node, vfile2_node]
        
        # Get virtual files
        with patch('app.core.virtual_folder.VirtualFile') as mock_vfile_class:
            mock_vfiles = [Mock(spec=VirtualFile), Mock(spec=VirtualFile)]
            mock_vfile_class.side_effect = mock_vfiles
            
            virtual_files = self.virtual_folder.get_virtual_files()
        
        # Verify results
        assert len(virtual_files) == 2
        assert all(isinstance(vf, VirtualFile) for vf in virtual_files)
        
        # Verify correct database call
        mock_db.nodes.find_related.assert_called_once_with(
            start_node_id=self.virtual_folder.id,
            edge_collection=mock_db.virtual_contains_edges,
            filter_by_type="virtual_file"
        )
    
    def test_custom_virtual_file_name(self):
        """Test specifying a custom virtual file name."""
        # Create mock function
        func_node = Mock(spec=node.FunctionNode)
        func_node.id = "func_1"
        func_node.name = "calculate_tax"
        
        function = Function(func_node)
        
        # Mock the add_virtual_file method
        with patch.object(self.virtual_folder, 'add_virtual_file') as mock_add_vfile:
            mock_virtual_file = Mock(spec=VirtualFile)
            mock_virtual_file.id = "custom_vfile"
            mock_virtual_file.name = "tax_calculations"
            mock_virtual_file.qname = "project.test_virtual_folder.tax_calculations"
            mock_virtual_file.add_code_element_with_dependencies.return_value = {
                'functions': [{'id': 'func_1', 'name': 'calculate_tax', 'qname': 'module.calculate_tax'}],
                'classes': [],
                'packages': [],
                'total_count': 1
            }
            mock_add_vfile.return_value = mock_virtual_file
            
            # Add code element with custom file name
            result = self.virtual_folder.add_code_element_with_dependencies(
                element=function,
                virtual_file_name="tax_calculations",
                include_dependencies=False
            )
        
        # Verify custom name was used
        mock_add_vfile.assert_called_once_with(
            file_name="tax_calculations",
            description="Virtual file containing calculate_tax and its dependencies"
        )
        assert result['virtual_file']['name'] == 'tax_calculations'
    
    def test_element_name_in_description(self):
        """Test that the element name appears in the virtual file description."""
        # Create mock class
        class_node = Mock(spec=node.ClassNode)
        class_node.id = "class_1"
        class_node.name = "PaymentProcessor"
        
        payment_class = Class(class_node)
        
        # Mock the add_virtual_file method to capture the description
        with patch.object(self.virtual_folder, 'add_virtual_file') as mock_add_vfile:
            mock_virtual_file = Mock(spec=VirtualFile)
            mock_virtual_file.add_code_element_with_dependencies.return_value = {
                'functions': [],
                'classes': [{'id': 'class_1', 'name': 'PaymentProcessor', 'qname': 'module.PaymentProcessor'}],
                'packages': [],
                'total_count': 1
            }
            mock_add_vfile.return_value = mock_virtual_file
            
            # Add code element
            self.virtual_folder.add_code_element_with_dependencies(
                element=payment_class,
                include_dependencies=True
            )
        
        # Verify description contains element name
        call_args = mock_add_vfile.call_args
        description = call_args[1]['description']
        assert 'PaymentProcessor' in description
        assert 'dependencies' in description 