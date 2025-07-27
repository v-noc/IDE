# Complex project specific tests
import pytest
from app.core.parser.project_scanner import ProjectScanner
from app.db import collections
from app.core.code_elements import Class, Function

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
    all_nodes = collections.nodes.find({"node_type": "class"})
    for node in all_nodes:
        class_obj = Class(node)
        if class_obj.name == "DatabaseManager":
            assert len(class_obj.methods) == 10, "DatabaseManager should have 10 methods"

            methods = [method.name for method in class_obj.methods]
            list_of_methods = ["__init__","_setup_tables","save","find","find_one","update","delete","count","_generate_id","_log_error"]
            for method in list_of_methods:
                assert method in methods, f"Method {method} not found in DatabaseManager"
            
            assert len(class_obj.fields) == 0, "DatabaseManager should have 0 fields"
            
        elif class_obj.name == "CacheManager":
            assert len(class_obj.methods) == 7, "CacheManager should have 10 methods"
            
            methods = [method.name for method in class_obj.methods]
            list_of_methods = ["__init__", "set", "get", "delete", "clear", "exists", "size"]
            for method in list_of_methods:
                assert method in methods, f"Method {method} not found in CacheManager"

        # for method in methods:
        #     method_obj = Function(method)
        #     print(f"method: {method_obj.name}")
        #     print(f"method.qname: {method_obj.qname}")
             
                    