# tests/unit/test_graph_builder.py

import pytest
from unittest.mock import MagicMock
from app.services.builder import GraphBuilder
from app.core.project import Project
from app.models import node, properties

def test_graph_builder_unit(mocker):
    """
    Unit test for GraphBuilder that ensures it calls the CodeGraphManager correctly
    without touching the database.
    """
    # 1. Arrange
    # Mock the CodeGraphManager dependency
    mock_manager = MagicMock()
    mocker.patch('app.services.builder.CodeGraphManager', return_value=mock_manager)

    # Mock the return value for the create_project call
    mock_project_node = node.ProjectNode(
        id="nodes/123",
        key="123",
        name="test_project",
        qname="/fake/path/test_project",
        properties=properties.ProjectProperties(path="/fake/path/test_project")
    )
    mock_project = Project(mock_project_node)
    mock_manager.create_project.return_value = mock_project

    # Instantiate the builder
    builder = GraphBuilder()
    
    # 2. Act
    project_path = "/fake/path/test_project"
    project = builder.build_graph_for_project(project_path)

    # 3. Assert
    # Check that a project was returned
    assert project is not None
    assert project.name == "test_project"

    # Verify that the manager's methods were called with the correct arguments
    mock_manager.create_project.assert_called_once_with(name="test_project", path=project_path)
    mock_manager.process_project_structure.assert_called_once_with(mock_project)
