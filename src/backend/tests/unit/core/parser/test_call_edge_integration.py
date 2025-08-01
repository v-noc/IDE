# Test CallEdge integration with project scanning and symbol resolution
import pytest
import tempfile
from pathlib import Path

from app.core.parser.project_scanner import ProjectScanner
from app.db import collections

# Mark all tests in this file as using the 'clear_db' fixture
pytestmark = pytest.mark.usefixtures("clear_db")


@pytest.fixture
def simple_call_project():
    """Create a temporary project with function calls for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create main.py with function calls
        main_py = project_path / "main.py"
        main_py.write_text("""
def helper_function():
    return "helper result"

def another_function():
    return "another result"

def main_function():
    # First call - should have order 0
    result1 = helper_function()
    
    # Second call - should have order 1  
    result2 = another_function()
    
    # Third call - should have order 2
    result3 = helper_function()
    
    return result1 + result2 + result3

class MyClass:
    def method_one(self):
        return "method one"
    
    def method_two(self):
        # Call to another method - should have order 0
        return self.method_one()

if __name__ == "__main__":
    main_function()
""")
        
        yield str(project_path)


def test_function_call_detection_and_ordering(simple_call_project):
    """
    Test that function calls are detected, resolved, and ordered correctly.
    """
    # Scan the project
    scanner = ProjectScanner(simple_call_project)
    scanner.scan()
    
    # Get all call edges
    call_edges = collections.calls_edges.find({})
    
    # Should have call edges for the function calls
    assert len(call_edges) > 0, "Should detect function calls"
    
    # Find the main_function node
    main_func_node = collections.nodes.find_one({
        "qname": "main.main_function"
    })
    assert main_func_node is not None, "Should find main_function"
    
    # Find calls from main_function
    main_func_calls = collections.calls_edges.find({
        "_from": main_func_node.id
    })
    
    # Should have 3 calls from main_function
    assert len(main_func_calls) == 3, (
        "main_function should have 3 calls"
    )
    
    # Verify call ordering
    calls_by_order = sorted(main_func_calls, key=lambda x: x.order)
    
    # First call should be to helper_function
    first_call = calls_by_order[0]
    assert first_call.order == 0
    first_target = collections.nodes.get(first_call.to_id)
    assert first_target.qname == "main.helper_function"
    
    # Second call should be to another_function
    second_call = calls_by_order[1]
    assert second_call.order == 1
    second_target = collections.nodes.get(second_call.to_id)
    assert second_target.qname == "main.another_function"
    
    # Third call should be to helper_function again
    third_call = calls_by_order[2]
    assert third_call.order == 2
    third_target = collections.nodes.get(third_call.to_id)
    assert third_target.qname == "main.helper_function"


def test_method_call_detection(simple_call_project):
    """
    Test that method calls within classes are detected correctly.
    """
    # Scan the project
    scanner = ProjectScanner(simple_call_project)
    scanner.scan()
    
    
    # Find the method_two node
    method_two_node = collections.nodes.find_one({
        "qname": "main.MyClass.method_two"
    })
    assert method_two_node is not None, "Should find method_two"
    
    # Find calls from method_two
    method_calls = collections.calls_edges.find({
        "_from": method_two_node.id
    })
    
    # Should have 1 call from method_two
    assert len(method_calls) == 1, "method_two should have 1 call"
    
    # Verify the call is to method_one
    call = method_calls[0]
    assert call.order == 0
    target = collections.nodes.get(call.to_id)
    assert target.qname == "main.MyClass.method_one"


def test_call_position_tracking(simple_call_project):
    """
    Test that call positions are correctly tracked.
    """
    # Scan the project
    scanner = ProjectScanner(simple_call_project)
    scanner.scan()
    
    # Get all call edges
    call_edges = collections.calls_edges.find({})
    
    # All edges should have position information
    for edge in call_edges:
        assert hasattr(edge, 'position'), "Edge should have position"
        assert edge.position.line_no > 0, (
            "Position should have valid line number"
        )
        assert edge.position.col_offset >= 0, "Position should have valid column"


def test_no_duplicate_call_edges(simple_call_project):
    """
    Test that duplicate call edges are not created for the same call.
    """
    # Scan the project
    scanner = ProjectScanner(simple_call_project)
    scanner.scan()
    
    # Get all call edges
    call_edges = collections.calls_edges.find({})
    
    # Check for duplicate edges (same from, to, and position)
    edge_signatures = set()
    
    for edge in call_edges:
        signature = (
            edge.from_id, 
            edge.to_id, 
            edge.position.line_no, 
            edge.position.col_offset
        )
        assert signature not in edge_signatures, (
            f"Duplicate edge detected: {signature}"
        )
        edge_signatures.add(signature) 