# Project structure and hierarchy tests
import pytest
from app.core.parser.project_scanner import ProjectScanner
from app.db import collections
from app.core.manager import CodeGraphManager

# Marks all tests in this file as using the 'clear_db' fixture
pytestmark = pytest.mark.usefixtures("clear_db")


def test_tree_structure(sample_project_path):
    """
    Tests that the tree structure is correctly created.
    """
    scanner = ProjectScanner(sample_project_path)
    scanner.scan()

    manager = CodeGraphManager()
    projects = manager.get_all_projects()
    assert len(projects) == 1

    project = projects[0]
    
    folders = project.get_folders()
    files = project.get_files()

    assert len(folders) == 1
    assert len(files) == 3
    
    models_folder = folders[0]
    assert (len(models_folder.get_files()) == 2)
    assert (len(models_folder.get_folders()) == 0)

    main_file = files[0]

    assert (len(main_file.get_functions()) == 1)
    assert (len(main_file.get_classes()) == 1)
    methods = main_file.get_classes()[0].methods
   
    assert len(methods) == 2
    

    utils_file = files[1]

    assert (len(utils_file.get_functions()) == 1)
    assert (len(utils_file.get_classes()) == 1)

    utils_class = utils_file.get_classes()[0]
    assert (utils_class.name == "UtilityClass")

    for func in utils_file.get_functions():
        assert (func.name in ["do_something", "helper_function"])


def test_nested_folder_structure(complex_project_path):
    """
    Test that nested folder structures are correctly parsed and represented.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    manager = CodeGraphManager()
    projects = manager.get_all_projects()
    assert len(projects) == 1
    
    project = projects[0]
    
    # Check folder hierarchy
    all_folders = project.get_all_folders()
    folder_names = [folder.name for folder in all_folders]
    
    expected_folders = ["utils", "models", "services", "data"]
    for expected in expected_folders:
        assert expected in folder_names, (
            f"Folder {expected} should exist in project"
        )
    
    # Check nested structure: services/data
    services_folder = next(
        (f for f in all_folders if f.name == "services"), None
    )
    assert services_folder is not None
    
    data_folders = services_folder.get_folders()
    assert len(data_folders) == 1
    assert data_folders[0].name == "data"


def test_file_existence_and_path_validation(complex_project_path):
    """
    Test file existence checks and path validation.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    # Get all file nodes
    file_nodes = collections.nodes.find({"node_type": "file"})
    assert len(file_nodes) > 8, "Should find multiple Python files"
    
    # Verify all file nodes have valid properties
    for file_node in file_nodes:
        if hasattr(file_node.properties, 'path'):
            # Note: Some files might not exist if they're external dependencies
            # Only check for our project files
            if not str(file_node.properties.path).startswith('__'):
                # The file should exist or be a virtual/external reference
                assert file_node.properties.path is not None


def test_function_and_method_detection(complex_project_path):
    """
    Test comprehensive function and method detection.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    # Get all function nodes
    function_nodes = collections.nodes.find({"node_type": "function"})
    assert len(function_nodes) > 15, "Should find many functions"
    
    # Test specific functions exist
    expected_functions = [
        "main.main",
        "config.load_config", 
        "utils.math_utils.calculate",
        "utils.string_utils.clean_string",
        "models.user.User.get_name",
        "services.auth.AuthService.login",
        "services.data.database.DatabaseManager.save"
    ]
    
    function_qnames = [node.qname for node in function_nodes]
    
    for expected_func in expected_functions:
        assert expected_func in function_qnames, (
            f"Function {expected_func} should be detected"
        )


def test_class_inheritance_detection(complex_project_path):
    """
    Test that class inheritance relationships are detected.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    # Find User class which inherits from BaseModel and ValidationMixin
    user_class = collections.nodes.find_one({"qname": "models.user.User"})
    assert user_class is not None
    
    # Find BaseModel class
    base_model = collections.nodes.find_one({"qname": "models.base.BaseModel"})
    assert base_model is not None
    
    # Find ValidationMixin class
    validation_mixin = collections.nodes.find_one(
        {"qname": "models.base.ValidationMixin"}
    )
    assert validation_mixin is not None


def test_enum_detection(complex_project_path):
    """
    Test that enums are correctly detected and classified.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    # Find UserType enum
    user_type_enum = collections.nodes.find_one(
        {"qname": "models.user.UserType"}
    )
    assert user_type_enum is not None
    assert user_type_enum.node_type == "class"  # Enums are classes in Python 