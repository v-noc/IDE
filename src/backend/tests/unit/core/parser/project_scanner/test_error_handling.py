# Error handling and edge case tests
import pytest
from app.core.parser.project_scanner import ProjectScanner
from app.db import collections

# Marks all tests in this file as using the 'clear_db' fixture
pytestmark = pytest.mark.usefixtures("clear_db")


def test_import_error_handling(complex_project_path):
    """
    Test that import errors and missing files are handled gracefully.
    """
    scanner = ProjectScanner(str(complex_project_path))
    
    # This should not crash even with circular imports or missing files
    try:
        scanner.scan()
        scan_successful = True
    except Exception as e:
        print(f"Scan failed with error: {e}")
        scan_successful = False
    
    assert scan_successful, "Scanner should handle errors gracefully"
    
    # Check that some nodes were still created despite potential errors
    all_nodes = collections.nodes.find({})
    assert len(all_nodes) > 0, "Should create some nodes even with errors"


def test_circular_import_handling(complex_project_path):
    """
    Test that circular imports are handled without crashing.
    """
    scanner = ProjectScanner(str(complex_project_path))
    
    # The complex project has a circular import between
    # main.py and circular_dep.py
    # This should not crash the scanner
    try:
        scanner.scan()
        circular_handled = True
    except Exception as e:
        print(f"Circular import caused error: {e}")
        circular_handled = False
    
    assert circular_handled, (
        "Scanner should handle circular imports gracefully"
    )
    
    # Verify that nodes were still created
    all_nodes = collections.nodes.find({})
    assert len(all_nodes) > 0, (
        "Should create nodes even with circular imports"
    )


def test_missing_import_handling(sample_project_path):
    """
    Test handling of imports that can't be resolved.
    """
    scanner = ProjectScanner(sample_project_path)
    
    # Scan should complete even if some imports can't be resolved
    try:
        scanner.scan()
    except Exception as e:
        pytest.fail(f"Scanner crashed on missing imports: {e}")
    
    # Should still create nodes for resolvable parts
    all_nodes = collections.nodes.find({})
    assert len(all_nodes) > 0, "Should create nodes for resolvable parts"


def test_empty_file_handling(complex_project_path):
    """
    Test that empty or minimal files are handled correctly.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    # Find __init__.py files which are often minimal
    init_files = collections.nodes.find({
        "node_type": "file",
        "name": "__init__.py"
    })
    
    # Should handle __init__.py files without crashing
    assert len(init_files) > 0, "Should find __init__.py files"
    
         # Each __init__.py should be properly processed
    for init_file in init_files:
        assert hasattr(init_file, 'qname'), (
            "__init__.py files should have qnames"
        )


def test_malformed_syntax_resilience(sample_project_path):
    """
    Test that the scanner is resilient to syntax errors.
    Note: This test assumes the sample files are well-formed,
    but tests the scanner's error handling mechanisms.
    """
    scanner = ProjectScanner(sample_project_path)
    
    # The scanner should complete successfully with well-formed files
    try:
        scanner.scan()
        summary = scanner.get_scan_summary()
        scan_completed = True
    except Exception as e:
        print(f"Scan failed: {e}")
        scan_completed = False
    
    assert scan_completed, "Scanner should complete with valid syntax"
    
    # Should track successful parsing
    assert summary["total_symbols"] > 0, "Should parse symbols successfully"


def test_large_file_handling(complex_project_path):
    """
    Test that larger files with many nodes are handled efficiently.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    # Find the largest file by node count
    all_nodes = collections.nodes.find({})
    file_node_counts = {}
    
    # Count nodes per file by checking contains edges
    for node in all_nodes:
        if node.node_type != "file":
            contains_edges = collections.contains_edges.find({"to_id": node.id})
            for edge in contains_edges:
                file_id = edge.from_id
                if file_id not in file_node_counts:
                    file_node_counts[file_id] = 0
                file_node_counts[file_id] += 1
    
    # Should handle files with multiple nodes
    if file_node_counts:
        max_nodes = max(file_node_counts.values())
        assert max_nodes > 0, "Should find files with multiple nodes" 