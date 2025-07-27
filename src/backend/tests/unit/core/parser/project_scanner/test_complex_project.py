# Complex project specific tests
import pytest
from app.core.parser.project_scanner import ProjectScanner
from app.db import collections

# Marks all tests in this file as using the 'clear_db' fixture
pytestmark = pytest.mark.usefixtures("clear_db")


def test_complex_project_structure_and_imports(complex_project_path):
    """
    Test complex project with nested folders, various import patterns,
    and comprehensive structure analysis.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    # Get all nodes for analysis
    all_nodes = collections.nodes.find({})
    
    # Test node count - should have many more nodes due to complex structure
    assert len(all_nodes) > 20, "Complex project should have many nodes"
    
    # Verify specific complex nodes exist
    app_class = collections.nodes.find_one({"qname": "main.Application"})
    assert app_class is not None
    assert app_class.node_type == "class"
    
    auth_service = collections.nodes.find_one(
        {"qname": "services.auth.AuthService"}
    )
    assert auth_service is not None
    assert auth_service.node_type == "class"
    
    db_manager = collections.nodes.find_one(
        {"qname": "services.data.database.DatabaseManager"}
    )
    assert db_manager is not None
    assert db_manager.node_type == "class"


def test_complex_project_comprehensive_analysis(
    complex_project_path, scanner_test_utils
):
    """
    Comprehensive analysis of the complex project structure.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    all_nodes = collections.nodes.find({})
    
    # Analyze node distribution
    node_counts = {
        'file': scanner_test_utils.count_nodes_by_type(all_nodes, 'file'),
        'class': scanner_test_utils.count_nodes_by_type(all_nodes, 'class'),
        'function': scanner_test_utils.count_nodes_by_type(
            all_nodes, 'function'
        ),
        'package': scanner_test_utils.count_nodes_by_type(
            all_nodes, 'package'
        ),
    }
    
   
    
    # Complex project should have substantial content
    assert node_counts['file'] > 8, "Should have many files"
    assert node_counts['class'] > 10, "Should have many classes"
    assert node_counts['function'] > 20, "Should have many functions"
    assert node_counts['package'] > 0, "Should have external packages"


def test_complex_project_service_layer(complex_project_path):
    """
    Test that the service layer in complex project is properly analyzed.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    # Find all service-related nodes
    service_nodes = collections.nodes.find_like("qname", "%services%")
    
    assert len(service_nodes) > 5, "Should find multiple service components"
    
    # Check specific service classes
    expected_services = [
        "services.auth.AuthService",
        "services.auth.PermissionService", 
        "services.data.database.DatabaseManager",
        "services.data.cache.CacheManager"
    ]
    
    for service_qname in expected_services:
        service_node = collections.nodes.find_one({"qname": service_qname})
        assert service_node is not None, (
            f"Should find service: {service_qname}"
        )
        assert service_node.node_type == "class", (
            f"Service {service_qname} should be a class"
        )


def test_complex_project_model_layer(complex_project_path):
    """
    Test that the model layer in complex project is properly analyzed.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    # Find model-related nodes
    model_nodes = collections.nodes.find_like("qname", "%models%")
    
    assert len(model_nodes) > 5, "Should find multiple model components"
    
    # Check specific model classes
    expected_models = [
        "models.base.BaseModel",
        "models.base.ValidationMixin",
        "models.user.User",
        "models.user.UserType",
        "models.user.UserManager"
    ]
    
    for model_qname in expected_models:
        model_node = collections.nodes.find_one({"qname": model_qname})
        assert model_node is not None, (
            f"Should find model: {model_qname}"
        )
        assert model_node.node_type == "class", (
            f"Model {model_qname} should be a class"
        )


def test_complex_project_utility_modules(complex_project_path):
    """
    Test that utility modules in complex project are properly analyzed.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    # Find utility-related nodes
    util_nodes = collections.nodes.find_like("qname", "%utils%")
    
    
    assert len(util_nodes) > 5, "Should find multiple utility components"
    
    # Check specific utility functions and classes
    expected_utils = [
        "utils.math_utils.calculate",
        "utils.math_utils.MathCalculator",
        "utils.string_utils.clean_string",
        "utils.string_utils.StringProcessor"
    ]
    
    for util_qname in expected_utils:
        util_node = collections.nodes.find_one({"qname": util_qname})
        assert util_node is not None, (
            f"Should find utility: {util_qname}"
        )


def test_complex_project_scan_summary(complex_project_path):
    """
    Test scan summary for complex project provides comprehensive information.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    summary = scanner.get_scan_summary()
    
    assert "project_path" in summary
    assert "total_symbols" in summary
    assert "created_packages" in summary
    
    assert summary["total_symbols"] > 30, (
        "Should track many symbols in complex project"
    )
    assert len(summary["created_packages"]) > 3, (
        "Should create multiple package nodes"
    )
    
    print(f"Complex project scan summary: {summary}")


def test_complex_project_external_dependencies(complex_project_path):
    """
    Test that external dependencies are properly identified and handled.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    # Should create package nodes for external imports
    package_nodes = collections.nodes.find({"node_type": "package"})
    assert len(package_nodes) > 0, "Should create package nodes"
    
    # Check for specific packages used in complex project
    expected_packages = ["typing", "enum", "pathlib", "uuid", "hashlib"]
    package_qnames = [node.qname for node in package_nodes]
    
    found_packages = [
        pkg for pkg in expected_packages 
        if any(pkg in qname for qname in package_qnames)
    ]
    assert len(found_packages) > 2, (
        f"Should find several expected external packages, "
        f"found: {found_packages}"
    ) 