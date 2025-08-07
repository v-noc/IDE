from pprint import pprint
import pytest
from app.core.code_elements import Class, Function
from app.core.manager import CodeGraphManager
from app.core.parser.project_scanner import ProjectScanner
from app.db import collections

pytestmark = pytest.mark.usefixtures("clear_db")


def _assert_folder_structure(data, name, qname_prefix, children_count):
    """Asserts the basic structure of a virtual folder."""
    assert data['name'] == name
    assert data['qname'] == f'{qname_prefix}.{name}'
    assert len(data['children']) == children_count


def _assert_linked_element(data, expected_qname):
    """Asserts that a virtual folder is linked to the correct code element."""
    assert data['link_to']['qname'] == expected_qname


def test_virtual_folder_structure_from_code_element(sample_project_path):
    """
    Test that a virtual folder structure can be generated from a code element,
    and that the resulting JSON from get_descendant_tree is correct.
    """
    scanner = ProjectScanner(sample_project_path)
    scanner.scan()

    manager = CodeGraphManager()

    projects = manager.get_all_projects()
    assert len(projects) == 1
    project = projects[0]

    folder = project.add_virtual_folder(folder_name="register")
    folder2 = project.add_virtual_folder(folder_name="main")
    assert len(project.get_virtual_folders()) == 2, "VF not created"

    function_doc = collections.nodes.find_one({"qname": "main.start_app"})

    class_doc = collections.nodes.find_one({"qname": "main.MainApp"})
    assert class_doc, "Could not find class 'main.MainApp'"
    class_ = Class(class_doc)

    assert function_doc, "Could not find function 'main.start_app'"
    function = Function(function_doc)

    folder.create_folder_for_element(function)
    folder2.create_folder_for_element(class_)
    # data2 = folder2.get_descendant_tree()
    # pprint(data2)
    data = folder.get_descendant_tree()
    
    _assert_folder_structure(data, 'register', 'sample_project', 1)
    assert data['link_to'] is None

    start_app_folder = data['children'][0]
    _assert_folder_structure(
        start_app_folder, 'start_app', 'sample_project.register', 3
    )
    _assert_linked_element(start_app_folder, 'main.start_app')

    child_names = {child['name'] for child in start_app_folder['children']}
    assert child_names == {'run', 'MainApp', 'helper_function'}

    for child in start_app_folder['children']:
        if child['name'] == 'run':
            _assert_folder_structure(
                child, 'run', 'sample_project.register.start_app', 1
            )
            _assert_linked_element(child, 'main.MainApp.run')
            assert child['children'][0]['name'] == 'helper_function'
            _assert_linked_element(
                child['children'][0], 'utils.helper_function'
            )
        elif child['name'] == 'MainApp':
            _assert_folder_structure(
                child, 'MainApp', 'sample_project.register.start_app', 1
            )
            _assert_linked_element(child, 'main.MainApp')
            assert child['children'][0]['name'] == 'User'
            _assert_linked_element(
                child['children'][0], 'models.user.User'
            )
        elif child['name'] == 'helper_function':
            _assert_folder_structure(
                child,
                'helper_function',
                'sample_project.register.start_app',
                0
            )
            _assert_linked_element(child, 'utils.helper_function')

    start_app_imports = start_app_folder.get('imports', [])
    assert len(start_app_imports) > 0
    import_qnames = {imp['qname'] for imp in start_app_imports}
    assert 'utils.helper_function' in import_qnames
    assert 'utils' in import_qnames


def test_link_directly_to_virtual_folder(sample_project_path):
    """
    Tests that a code element can be linked directly to a virtual folder.
    """
    scanner = ProjectScanner(sample_project_path)
    scanner.scan()

    manager = CodeGraphManager()
    project = manager.get_all_projects()[0]

    function_doc = collections.nodes.find_one({"qname": "main.start_app"})
    assert function_doc, "Could not find function 'main.start_app'"
    function = Function(function_doc)

    folder = project.add_virtual_folder(folder_name="direct_link_test")
    folder.create_folder_for_element(function, link_directly=True)
    data = folder.get_descendant_tree()

    _assert_folder_structure(data, 'direct_link_test', 'sample_project', 3)
    _assert_linked_element(data, 'main.start_app')


def test_main_app_virtual_folder(sample_project_path):
    """
    Tests the structure of the virtual folder generated for the MainApp class.
    """
    scanner = ProjectScanner(sample_project_path)
    scanner.scan()

    manager = CodeGraphManager()
    project = manager.get_all_projects()[0]

    class_doc = collections.nodes.find_one({"qname": "main.MainApp"})
    assert class_doc, "Could not find class 'main.MainApp'"
    class_ = Class(class_doc)

    folder = project.add_virtual_folder(folder_name="main_app_test")
    folder.create_folder_for_element(class_)
    data = folder.get_descendant_tree()

    _assert_folder_structure(data, 'main_app_test', 'sample_project', 1)

    main_app_folder = data['children'][0]
    _assert_folder_structure(
        main_app_folder, 'MainApp', 'sample_project.main_app_test', 1
    )
    _assert_linked_element(main_app_folder, 'main.MainApp')

    main_app_class_data = main_app_folder['link_to']
    assert main_app_class_data['node_type'] == 'class'
    assert len(main_app_class_data['methods']) == 2
    method_names = {
        method['name'] for method in main_app_class_data['methods']
    }
    assert method_names == {'__init__', 'run'}

    user_folder = main_app_folder['children'][0]
    _assert_folder_structure(
        user_folder,
        'User',
        'sample_project.main_app_test.MainApp',
        0
    )
    _assert_linked_element(user_folder, 'models.user.User')

    user_class_data = user_folder['link_to']
    assert user_class_data['node_type'] == 'class'
   
    assert len(user_class_data['fields']) == 2
    field_names = {field['varname'] for field in user_class_data['fields']}
    assert field_names == {'name', 'age'}
    assert len(user_class_data['methods']) == 1
    assert user_class_data['methods'][0]['name'] == 'get_name'
   

   
  