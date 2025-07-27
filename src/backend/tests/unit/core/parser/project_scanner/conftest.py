# Shared fixtures for project scanner tests
import pytest
from pathlib import Path


@pytest.fixture
def sample_project_path():
    """Returns the path to the sample project directory."""
    return str(Path(__file__).parent.parent / "sample_project")


@pytest.fixture
def complex_project_path():
    """Returns the path to the complex test project."""
    return Path(__file__).parent.parent / "complex_project"


@pytest.fixture
def scanner_test_utils():
    """Utility functions for scanner tests."""
    class ScannerTestUtils:
        @staticmethod
        def count_nodes_by_type(nodes, node_type):
            """Count nodes of a specific type."""
            return len([n for n in nodes if n.node_type == node_type])
        
        @staticmethod
        def find_node_by_qname(nodes, qname):
            """Find a node by its qualified name."""
            return next((n for n in nodes if n.qname == qname), None)
        
        @staticmethod
        def get_import_edges_by_target(edges, target_pattern):
            """Get import edges matching a target pattern."""
            return [
                edge for edge in edges 
                if target_pattern in edge.target_qname
            ]
    
    return ScannerTestUtils() 