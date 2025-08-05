
import pytest
from app.core.code_elements import Function
from app.core.manager import CodeGraphManager
from app.core.parser.project_scanner import ProjectScanner
from app.db import collections

pytestmark = pytest.mark.usefixtures("clear_db")


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
    assert len(project.get_virtual_folders()) == 1, "VF not created"

    function_doc = collections.nodes.find_one({"qname": "main.start_app"})
    assert function_doc, "Could not find function 'main.start_app'"
    function = Function(function_doc)

    folder.create_folder_for_element(function)

    data = folder.get_descendant_tree()

    assert data['name'] == 'register'
    assert data['qname'] == 'sample_project.register'
    assert data['link_to'] is None
    assert len(data['children']) == 1

    start_app_folder = data['children'][0]
    assert start_app_folder['name'] == 'start_app'
    qname = start_app_folder['qname']
    assert qname == 'sample_project.register.start_app'
    assert start_app_folder['link_to']['qname'] == 'main.start_app'
    assert len(start_app_folder['children']) == 3

    child_names = {child['name'] for child in start_app_folder['children']}
    assert child_names == {'run', 'MainApp', 'helper_function'}

    for child in start_app_folder['children']:
        if child['name'] == 'run':
            assert child['link_to']['qname'] == 'main.MainApp.run'
            assert len(child['children']) == 1
            assert child['children'][0]['name'] == 'helper_function'
            run_child_qname = child['children'][0]['link_to']['qname']
            assert run_child_qname == 'utils.helper_function'
        elif child['name'] == 'MainApp':
            assert child['link_to']['qname'] == 'main.MainApp'
            assert len(child['children']) == 1
            assert child['children'][0]['name'] == 'User'
            main_app_child_qname = child['children'][0]['link_to']['qname']
            assert main_app_child_qname == 'models.user.User'
        elif child['name'] == 'helper_function':
            assert child['link_to']['qname'] == 'utils.helper_function'
            assert not child['children']

    start_app_imports = start_app_folder.get('imports', [])
    assert len(start_app_imports) > 0
    import_qnames = {imp['qname'] for imp in start_app_imports}
    assert 'utils.helper_function' in import_qnames
    assert 'utils' in import_qnames
   

   
  