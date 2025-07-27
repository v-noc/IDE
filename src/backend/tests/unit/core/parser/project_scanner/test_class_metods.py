# Complex project specific tests
import pytest
from app.core.parser.project_scanner import ProjectScanner
from app.db import collections
from app.core.code_elements import Class, Function, Package

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

    # all_packages = collections.nodes.find({"node_type": "package"})
    # for package in all_packages:
    #     package_obj = Package(package)
    #     print(f"package: {package_obj.name} {package_obj.qname}")
    #     importers = package_obj.get_nodes_that_import_this()
    #     for importer in importers:
    #         print(f"importer: {importer.qname} from {package_obj.qname}")

    for node in all_nodes:
        class_obj = Class(node)
        if class_obj.name == "DatabaseManager":
            assert len(class_obj.methods) == 10, "DatabaseManager should have 10 methods"

            methods = [method.name for method in class_obj.methods]
            for method in class_obj.methods:
                calls = method.get_function_calls()
                class_calls = method.get_class_calls()
                caller_functions = method.get_node_caller_functions()
                caller_classes = method.get_node_caller_classes()
                for call in calls:
                    print(f" call: {call.name} from {method.name}")
                for call in class_calls:
                    print(f" class call: {call.name} from {method.name}")
                for caller_function in caller_functions:
                    print(f" caller function: {caller_function.name} from {method.name}")
                for caller_class in caller_classes:
                    print(f" caller class: {caller_class.name} from {method.name}")
            
            list_of_methods = ["__init__","_setup_tables","save","find","find_one","update","delete","count","_generate_id","_log_error"]
            for method in list_of_methods:
                
                assert method in methods, f"Method {method} not found in DatabaseManager"
            
            assert len(class_obj.fields) == 0, "DatabaseManager should have 0 fields"
            
        elif class_obj.name == "CacheManager":
            class_caller = class_obj.get_node_caller_functions()
            class_caller_classes = class_obj.get_node_caller_classes()
            class_calls = class_obj.get_class_calls()
            class_calls_functions = class_obj.get_function_calls()
            print("--------------------------------")
            for class_call in class_calls:
                print(f" class call: {class_call.qname} from {class_obj.qname}")
            for class_call_function in class_calls_functions:
                print(f" class call function: {class_call_function.qname} from {class_obj.qname}")
            for class_caller_function in class_caller:
                print(f" class caller function: {class_caller_function.qname} from {class_obj.qname}")
            for class_caller_class in class_caller_classes:
                print(f" class caller class: {class_caller_class.qname} from {class_obj.qname}")
            print("--------------------------------")
            assert len(class_obj.methods) == 7, "CacheManager should have 10 methods"
            for method in class_obj.methods:
                calls = method.get_function_calls()
                class_calls = method.get_class_calls()
                package_calls = method.get_package_calls()
                caller_functions = method.get_node_caller_functions()
                caller_classes = method.get_node_caller_classes()
                for call in calls:
                    print(f" call: {call.name} from {method.name}")
                for call in class_calls:
                    print(f" class call: {call.name} from {method.name}")
                for package_call in package_calls:
                    print(f" package call: {package_call.name} from {method.name}")
                for caller_function in caller_functions:
                    print(f" caller function: {caller_function.name} from {method.name}")
                for caller_class in caller_classes:
                    print(f" caller class: {caller_class.name} from {method.name}")
            methods = [method.name for method in class_obj.methods]
            list_of_methods = ["__init__", "set", "get", "delete", "clear", "exists", "size"]
            for method in list_of_methods:
                assert method in methods, f"Method {method} not found in CacheManager"

        # for method in methods:
        #     method_obj = Function(method)
        #     print(f"method: {method_obj.name}")
        #     print(f"method.qname: {method_obj.qname}")
             
                    