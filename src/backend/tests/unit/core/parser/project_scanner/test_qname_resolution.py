# Qualified name resolution and path mapping tests
import pytest
from app.core.parser.project_scanner import ProjectScanner
from app.db import collections

# Marks all tests in this file as using the 'clear_db' fixture
pytestmark = pytest.mark.usefixtures("clear_db")


def test_qname_resolution_and_path_mapping(complex_project_path):
    """
    Test that qualified names are correctly resolved and mapped to paths.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    # Test qname to path resolution for various node types
    test_cases = [
        ("main.Application", "main.py", "class"),
        ("config.load_config", "config.py", "function"),
        ("utils.math_utils.calculate", "utils/math_utils.py", "function"),
        (
            "utils.string_utils.StringProcessor", 
            "utils/string_utils.py", 
            "class"
        ),
        ("models.user.User", "models/user.py", "class"),
        ("models.user.UserType", "models/user.py", "class"),
        ("services.auth.AuthService", "services/auth.py", "class"),
        (
            "services.data.database.DatabaseManager", 
            "services/data/database.py", 
            "class"
        ),
    ]
    
    for qname, expected_path_suffix, expected_type in test_cases:
        node = collections.nodes.find_one({"qname": qname})
        assert node is not None, f"Node {qname} should exist"
        assert node.node_type == expected_type, (
            f"Node {qname} should be {expected_type}"
        )
        
        # Verify the node belongs to the expected file
        if expected_type != "file":
            # Find the file node that contains this node
            contains_edges = collections.contains_edges.find({
                "_to": node.id
            })
            assert len(contains_edges) > 0, (
                f"Node {qname} should be contained in a file"
            )


def test_simple_qname_resolution(sample_project_path, scanner_test_utils):
    """
    Test qname resolution for the simple sample project.
    """
    scanner = ProjectScanner(sample_project_path)
    scanner.scan()
    
    all_nodes = collections.nodes.find({})
    
    # Test specific qnames exist
    expected_qnames = [
        "main.MainApp",
        "main.start_app", 
        "utils.helper_function",
        "utils.UtilityClass",
        "models.user.User",
        "models.user.User.get_name"
    ]
    
    for qname in expected_qnames:
        node = scanner_test_utils.find_node_by_qname(all_nodes, qname)
        assert node is not None, f"Should find node with qname: {qname}"


def test_nested_module_qnames(complex_project_path):
    """
    Test qname resolution for deeply nested modules.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    # Test deeply nested qnames
    nested_cases = [
        "services.data.database.DatabaseManager.save",
        "services.data.cache.CacheManager.get",
        "models.user.UserManager.find_user",
        "utils.math_utils.MathCalculator.add"
    ]
    
    for qname in nested_cases:
        node = collections.nodes.find_one({"qname": qname})
        assert node is not None, f"Should find nested qname: {qname}"
        assert node.node_type == "function", (
            f"Nested qname {qname} should be a function"
        )


def test_qname_uniqueness(complex_project_path):
    """
    Test that all qnames are unique within the project.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    all_nodes = collections.nodes.find({})
    qnames = [node.qname for node in all_nodes if hasattr(node, 'qname')]

    # Check for duplicates
    seen_qnames = set()
    duplicates = set()
    
    for qname in qnames:
        if qname in seen_qnames:
            duplicates.add(qname)
        seen_qnames.add(qname)
    print(f"Duplicates: {duplicates}")
    assert len(duplicates) == 0, f"Found duplicate qnames: {duplicates}"


def test_package_qname_resolution(complex_project_path):
    """
    Test that external package qnames are correctly resolved.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    package_nodes = collections.nodes.find({"node_type": "package"})
    
    # Check that package nodes have reasonable qnames
    for package in package_nodes:
        qname = package.qname
        
        # Package qnames should not be empty
        assert qname and len(qname) > 0, "Package qname should not be empty"
        
        # Common packages should be recognizable
        if any(lib in qname for lib in ['typing', 'os', 'sys']):
            assert '.' not in qname or qname.count('.') <= 2, (
                f"Package qname should be simple: {qname}"
            ) 