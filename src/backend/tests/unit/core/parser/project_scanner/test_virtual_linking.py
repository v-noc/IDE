import json
from pprint import pprint
import pytest
from app.core.code_elements import Class, Function
from app.core.file import File
from app.core.manager import CodeGraphManager
from app.core.parser.project_scanner import ProjectScanner
from app.db import collections
from app.core.virtual_folder import VirtualFolder
from app.core.folder import Folder

pytestmark = pytest.mark.usefixtures("clear_db")


def _assert_folder_structure(data, name, qname_prefix, children_count):
    """Asserts the basic structure of a virtual folder."""
    assert data['name'] == name
    assert data['qname'] == f'{qname_prefix}.{name}'
    assert len(data['children']) == children_count


def _assert_linked_element(data, expected_qname):
    """Asserts that a virtual folder is linked to the correct code element."""
    assert data['link_to']['qname'] == expected_qname


def _setup_test_project(sample_project_path):
    """Common setup for virtual folder tests."""
    scanner = ProjectScanner(sample_project_path)
    scanner.scan()

    manager = CodeGraphManager()
    projects = manager.get_all_projects()
    assert len(projects) == 1
    project = projects[0]

    function_doc = collections.nodes.find_one({"qname": "main.start_app"})
    assert function_doc, "Could not find function 'main.start_app'"
    function = Function(function_doc)

    class_doc = collections.nodes.find_one({"qname": "main.MainApp"})
    assert class_doc, "Could not find class 'main.MainApp'"
    class_ = Class(class_doc)

    return project, function, class_


def test_virtual_folder_structure_from_code_element(sample_project_path):
    """
    Test that a virtual folder structure can be generated from a code element,
    and that the resulting JSON from get_descendant_tree is correct.
    """
    project, function, class_ = _setup_test_project(sample_project_path)

    folder = project.add_virtual_folder(folder_name="register")
    folder2 = project.add_virtual_folder(folder_name="main")
    assert len(project.get_virtual_folders()) == 2, "VF not created"

    folder.create_folder_for_element(function)
    folder2.create_folder_for_element(class_)
    # data2 = folder2.get_descendant_tree()
    # pprint(data2)
    data = folder.get_descendant_tree()

    with open('data.json', 'w') as f:
        json.dump(data, f)
    
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
            # MainApp has two methods: __init__ and run
            _assert_folder_structure(
                child, 'MainApp', 'sample_project.register.start_app', 2
            )
            _assert_linked_element(child, 'main.MainApp')
            # Check for methods as children
            method_names = {c['name'] for c in child['children']}
            assert method_names == {'__init__', 'run'}
            # Check __init__ content
            init_method = next(
                c for c in child['children'] if c['name'] == '__init__'
            )
            _assert_folder_structure(
                init_method,
                '__init__',
                'sample_project.register.start_app.MainApp',
                1
            )
            _assert_linked_element(init_method, 'main.MainApp.__init__')
            assert init_method['children'][0]['name'] == 'User'
            _assert_linked_element(
                init_method['children'][0], 'models.user.User'
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


def test_virtual_folder_structure_from_code_element_link_directly(
    sample_project_path
):
    """
    Test that a virtual folder structure can be generated from a code element
    with link_directly=True, where the element is linked directly to the folder
    and its dependencies are added as children.
    """
    project, function, class_ = _setup_test_project(sample_project_path)

    folder = project.add_virtual_folder(folder_name="register")
    assert len(project.get_virtual_folders()) == 1, "VF not created"

    folder.create_folder_for_element(function, link_directly=True)
    data = folder.get_descendant_tree()
    pprint(data)
    # When link_directly=True, the folder itself is linked to the element
    # and has the dependencies as direct children
    _assert_folder_structure(data, 'register', 'sample_project', 3)
    _assert_linked_element(data, 'main.start_app')

    # The dependencies should be direct children of the register folder
    child_names = {child['name'] for child in data['children']}
    assert child_names == {'run', 'MainApp', 'helper_function'}

    for child in data['children']:
        if child['name'] == 'run':
            _assert_folder_structure(
                child, 'run', 'sample_project.register', 1
            )
            _assert_linked_element(child, 'main.MainApp.run')
            assert child['children'][0]['name'] == 'helper_function'
            _assert_linked_element(
                child['children'][0], 'utils.helper_function'
            )
        elif child['name'] == 'MainApp':
            _assert_folder_structure(
                child, 'MainApp', 'sample_project.register', 2
            )
            _assert_linked_element(child, 'main.MainApp')
            method_names = {c['name'] for c in child['children']}
            assert method_names == {'__init__', 'run'}
            init_method = next(
                c for c in child['children'] if c['name'] == '__init__'
            )
            _assert_linked_element(init_method, 'main.MainApp.__init__')
            assert init_method['children'][0]['name'] == 'User'

        elif child['name'] == 'helper_function':
            _assert_folder_structure(
                child, 'helper_function', 'sample_project.register', 0
            )
            _assert_linked_element(child, 'utils.helper_function')

    # Check imports on the main folder since it's linked directly
    imports = data.get('imports', [])
    assert len(imports) > 0
    import_qnames = {imp['qname'] for imp in imports}
    assert 'utils.helper_function' in import_qnames
    assert 'utils' in import_qnames


def test_link_directly_to_virtual_folder(sample_project_path):
    """
    Tests that a code element can be linked directly to a virtual folder.
    """
    project, function, class_ = _setup_test_project(sample_project_path)

    folder = project.add_virtual_folder(folder_name="direct_link_test")
    folder.create_folder_for_element(function, link_directly=True)
    data = folder.get_descendant_tree()

    _assert_folder_structure(data, 'direct_link_test', 'sample_project', 3)
    _assert_linked_element(data, 'main.start_app')


def test_main_app_virtual_folder(sample_project_path):
    """
    Tests the structure of the virtual folder generated for the MainApp class.
    """
    project, function, class_ = _setup_test_project(sample_project_path)

    folder = project.add_virtual_folder(folder_name="main_app_test")
    folder.create_folder_for_element(class_)
    data = folder.get_descendant_tree()

    _assert_folder_structure(data, 'main_app_test', 'sample_project', 1)

    main_app_folder = data['children'][0]

    # MainApp class has 2 methods: __init__ and run
    _assert_folder_structure(
        main_app_folder, 'MainApp', 'sample_project.main_app_test', 2
    )
    _assert_linked_element(main_app_folder, 'main.MainApp')

    main_app_class_data = main_app_folder['link_to']
    assert main_app_class_data['node_type'] == 'class'
    # The 'children' now represent the methods
    assert len(main_app_folder['children']) == 2
    method_names = {
        method['name'] for method in main_app_folder['children']
    }
    assert method_names == {'__init__', 'run'}

    # Check the __init__ method's children
    init_method_folder = next(
        c for c in main_app_folder['children'] if c['name'] == '__init__'
    )
    _assert_folder_structure(
        init_method_folder,
        '__init__',
        'sample_project.main_app_test.MainApp',
        1
    )
    _assert_linked_element(init_method_folder, 'main.MainApp.__init__')

    user_folder = init_method_folder['children'][0]
    # The User class has 1 method: get_name
    _assert_folder_structure(
        user_folder,
        'User',
        'sample_project.main_app_test.MainApp.__init__',
        1
    )
    _assert_linked_element(user_folder, 'models.user.User')

    user_class_data = user_folder['link_to']
    assert user_class_data['node_type'] == 'class'

    assert len(user_class_data['fields']) == 2
    field_names = {field['varname'] for field in user_class_data['fields']}
    assert field_names == {'name', 'age'}
    # The user's method is now a child folder
    assert user_folder['children'][0]['name'] == 'get_name'
    _assert_linked_element(
        user_folder['children'][0], 'models.user.User.get_name'
    )


def test_delete_virtual_folder_cascade(sample_project_path):
    """
    Tests that deleting a virtual folder also deletes all its descendants
    and associated edges.
    """
    project, function, _ = _setup_test_project(sample_project_path)

    # Create a virtual folder and a nested structure within it
    folder = project.add_virtual_folder(folder_name="register")
    folder.create_folder_for_element(function)

    # Verify that folders and edges were created
    # Project root + 'register' + 4 descendants = 6
    initial_vf_count = len(
        list(collections.nodes.find({"node_type": "virtual_folder"}))
    )

    for node in collections.nodes.find({"node_type": "virtual_folder"}):
        pprint(node)

    assert initial_vf_count == 11, "Virtual folders not created"
    # 1 edge from root, 5 in the structure
    initial_edge_count = len(list(collections.virtual_contains_edges.find({})))
    assert initial_edge_count == 11
    
    # Get the descendant tree to find a folder to delete
    data = folder.get_descendant_tree()

    with open('data.json', 'w') as f:
        json.dump(data, f)

    start_app_folder_id = data['children'][0]['id']
    start_app_folder_doc = collections.nodes.get(
        start_app_folder_id
    )
    start_app_vf = VirtualFolder(start_app_folder_doc)

    # Count `links_to` edges before deletion
    initial_links_to_count = len(list(collections.links_to_edges.find({})))

    # Delete the 'start_app' virtual folder
    start_app_vf.delete()

    # After deletion:
    # Remaining VFs:  'register' folder = 1
    final_vf_count = len(
        list(collections.nodes.find({"node_type": "virtual_folder"}))
    )
    assert final_vf_count == 1
    
    # Remaining edges: project_root -> register (1 edge)
    final_edge_count = len(list(collections.virtual_contains_edges.find({})))
    assert final_edge_count == 1
    # Check that links_to edges were also deleted.
    final_links_to_count = len(list(collections.links_to_edges.find({})))
    assert final_links_to_count == initial_links_to_count - 10

   
def test_class_virtual_folder(sample_project_path):
    """
    Tests the structure of the virtual folder generated for a class.
    """
    project, function, class_ = _setup_test_project(sample_project_path)

    folder = project.add_virtual_folder(folder_name="class_test")
    folder.create_folder_for_element(class_)
    data = folder.get_descendant_tree()

    # The root should contain one child: the class folder
    _assert_folder_structure(data, 'class_test', 'sample_project', 1)
    class_folder = data['children'][0]

    # The class folder should have 2 methods as children
    _assert_folder_structure(
        class_folder, 'MainApp', 'sample_project.class_test', 2
    )
    _assert_linked_element(class_folder, 'main.MainApp')

    method_names = {child['name'] for child in class_folder['children']}
    assert method_names == {'__init__', 'run'}

    # The 'run' method should have one child: 'helper_function'
    run_folder = next(
        child for child in class_folder['children'] if child['name'] == 'run'
    )
    _assert_folder_structure(
        run_folder, 'run', 'sample_project.class_test.MainApp', 1
    )
    _assert_linked_element(run_folder, 'main.MainApp.run')
    assert run_folder['children'][0]['name'] == 'helper_function'

 
def test_virtual_folder_structure_from_file(sample_project_path):
    """
    Tests the structure of the virtual folder generated for a File.
    The file's dependency tree should include its classes and functions.
    """
    project, _, _ = _setup_test_project(sample_project_path)

    # Locate the main.py file node and wrap it as a File domain object
    file_doc = collections.nodes.find_one({
        "node_type": "file",
        "qname": "main",
    })
    assert file_doc, "Could not find file 'main.py'"
    file = File(file_doc)
    folder = project.add_virtual_folder(folder_name="file_test")
    folder.create_folder_for_element(file)
    data = folder.get_descendant_tree()
 
    _assert_folder_structure(data, "file_test", "sample_project", 1)

    file_folder = data["children"][0]
    # The file folder should have two children: MainApp (class) and start_app
    _assert_folder_structure(
        file_folder, "main.py", "sample_project.file_test", 2
    )
    assert file_folder["link_to"]["node_type"] == "file"
    assert file_folder["link_to"]["name"] == "main.py"

    child_names = {child["name"] for child in file_folder["children"]}
    assert child_names == {"MainApp", "start_app"}


def test_virtual_folder_structure_from_folder(sample_project_path):
    """
    Tests the structure of the virtual folder generated for a Folder.
    The folder's dependency tree should include its files and subfolders.
    """
    project, _, _ = _setup_test_project(sample_project_path)

    # Get a real folder from the scanned project (e.g., 'models')
    folder_doc = collections.nodes.find_one({
        "node_type": "folder",
        "qname": "models",
    })
    assert folder_doc, "Could not find folder 'models'"
    physical_folder = Folder(folder_doc)

    vf = project.add_virtual_folder(folder_name="folder_test")
    vf.create_folder_for_element(physical_folder)
    data = vf.get_descendant_tree()

    _assert_folder_structure(data, "folder_test", "sample_project", 1)

    models_vf = data["children"][0]
    assert models_vf["name"] == "models"
    assert models_vf["link_to"]["node_type"] == "folder"
    assert models_vf["link_to"]["qname"] == "models"
    assert len(models_vf["children"]) >= 1

    # Ensure the models folder contains the 'user.py' file as a child VF
    user_file_vf = next(
        (
            c for c in models_vf["children"]
            if c.get("link_to", {}).get("node_type") == "file"
            and c.get("link_to", {}).get("name") == "user.py"
        ),
        None,
    )
    assert user_file_vf is not None, "Expected 'user.py' under models folder"
    # And that the file expands to include the 'User' class
    child_names = {c["name"] for c in user_file_vf.get("children", [])}
    assert "User" in child_names