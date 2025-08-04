"""
Tests for VirtualFolder code element linking functionality.
"""
import pytest
from unittest.mock import Mock, patch
from app.core.virtual_folder import VirtualFolder
from app.core.code_elements import Function
from app.models import node
from arango.exceptions import DocumentInsertError


@pytest.mark.explicit
class TestVirtualFolderElementLinking:
    """Test suite for VirtualFolder element linking functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.virtual_folder_node = Mock(spec=node.VirtualFolderNode)
        self.virtual_folder_node.key = "vfolder_1"
        self.virtual_folder_node.id = "vfolder_1"
        self.virtual_folder_node.name = "test_virtual_folder"
        self.virtual_folder_node.qname = "project.test_virtual_folder"
        self.virtual_folder_node.description = "Test virtual folder"
        
        self.virtual_folder = VirtualFolder(self.virtual_folder_node)
    
    def test_create_folder_for_element(self):
        """
        Test that `create_folder_for_element` creates, names, and links a
        new folder.
        """
        mock_element_node = Mock(spec=node.FunctionNode)
        mock_element_node.id = "func_1"
        mock_element_node.name = "my_function"
        mock_element_node.description = "A test function"
        mock_element = Function(mock_element_node)

        mock_new_folder = Mock(spec=VirtualFolder)
        
        with patch.object(
            self.virtual_folder,
            'add_virtual_folder',
            return_value=mock_new_folder
        ) as mock_add_folder:
            
            result_folder = self.virtual_folder.create_folder_for_element(
                mock_element
            )

            mock_add_folder.assert_called_once_with(
                folder_name="my_function",
                description="A test function"
            )
            mock_new_folder.link_to_code_element.assert_called_once_with("func_1")
            assert result_folder is mock_new_folder
    
    @patch('app.core.virtual_folder.db')
    def test_link_to_code_element_success(self, mock_db):
        """Test successfully linking a folder to a code element."""
        mock_db.nodes.get.return_value = True

        self.virtual_folder.link_to_code_element("element_123")

        mock_db.links_to_edges.create.assert_called_once()
        created_edge = mock_db.links_to_edges.create.call_args[0][0]
        assert created_edge.from_id == self.virtual_folder.id
        assert created_edge.to_id == "element_123"

    @patch('app.core.virtual_folder.db')
    def test_link_to_code_element_not_found(self, mock_db):
        """Test linking to a non-existent code element raises ValueError."""
        mock_db.nodes.get.return_value = None

        with pytest.raises(ValueError, match="not found"):
            self.virtual_folder.link_to_code_element("non_existent_element")

    @patch('app.core.virtual_folder.db')
    def test_link_to_code_element_already_linked_raises_error(self, mock_db):
        """
        Test linking a folder that is already linked raises a ValueError.
        """
        mock_db.nodes.get.return_value = True
        # Simulate the ArangoDB error for a unique constraint violation
        mock_error = DocumentInsertError("Unique constraint violated")
        mock_error.error_code = 1210
        mock_db.links_to_edges.create.side_effect = mock_error

        with pytest.raises(ValueError, match="already linked"):
            self.virtual_folder.link_to_code_element("element_123")

    @patch('app.core.virtual_folder.db')
    def test_get_folder_linked_to_element_found(self, mock_db):
        """Test finding the folder linked to an element when a link exists."""
        mock_edge = Mock()
        mock_edge.from_id = "vfolder_123"
        mock_db.links_to_edges.find_one.return_value = mock_edge

        mock_folder_node = Mock(spec=node.VirtualFolderNode)
        mock_folder_node.node_type = 'virtual_folder'
        mock_db.nodes.get.return_value = mock_folder_node

        with patch('app.core.virtual_folder.VirtualFolder') as mock_vfolder_class:
            VirtualFolder.get_folder_linked_to_element("element_abc")
            
            mock_db.links_to_edges.find_one.assert_called_once_with(
                {"to_id": "element_abc"}
            )
            mock_db.nodes.get.assert_called_once_with("vfolder_123")
            mock_vfolder_class.assert_called_once_with(mock_folder_node)
    
    @patch('app.core.virtual_folder.db')
    def test_get_folder_linked_to_element_not_found(self, mock_db):
        """Test getting the folder for an unlinked element returns None."""
        mock_db.links_to_edges.find_one.return_value = None

        result = VirtualFolder.get_folder_linked_to_element("unlinked_element")

        assert result is None
        mock_db.nodes.get.assert_not_called() 