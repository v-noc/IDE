import pytest
from pprint import pprint
from app.core.manager import CodeGraphManager
from app.core.parser.project_scanner import ProjectScanner
from app.db import collections

pytestmark = pytest.mark.usefixtures("clear_db")

def _get_virtual_folder_data(project, element_qname, folder_name):
    """Helper to generate virtual folder data for a given code element."""
    element_doc = collections.nodes.find_one({"qname": element_qname})
    assert element_doc, f"Could not find element '{element_qname}'"
    
    from app.core.code_elements import to_domain_element
    element = to_domain_element(element_doc)
    
    folder = project.add_virtual_folder(folder_name=folder_name)
    folder.create_folder_for_element(element)
    return folder.get_descendant_tree()


def test_start_app_imports(sample_project_path):
    """
    Tests that the virtual folder for 'start_app' has the correct imports.
    """
    scanner = ProjectScanner(sample_project_path)
    scanner.scan()

    manager = CodeGraphManager()
    project = manager.get_all_projects()[0]
    
    data = _get_virtual_folder_data(project, "main.start_app", "start_app_test")
    
    start_app_folder = data['children'][0]
    assert start_app_folder['name'] == 'start_app'
    
    imports = start_app_folder.get('imports', [])
    assert len(imports) > 0, "No imports found for start_app"
    
    import_qnames = {imp['qname'] for imp in imports}
 
    assert 'utils.helper_function' in import_qnames
    assert 'utils' in import_qnames
    


def test_user_class_fields(sample_project_path):
    """
    Tests that the virtual folder for the 'User' class has correct fields.
    """
    scanner = ProjectScanner(sample_project_path)
    scanner.scan()

    manager = CodeGraphManager()
    project = manager.get_all_projects()[0]

    data = _get_virtual_folder_data(project, "models.user.User", "user_test")

    user_folder = data['children'][0]
    assert user_folder['name'] == 'User'

    linked_class = user_folder.get('link_to', {})
    assert linked_class, "User class not linked"
    
    fields = linked_class.get('fields', [])
    assert len(fields) == 2, "Incorrect number of fields"
    
    field_details = {
        field['varname']: field['varType'] for field in fields
    }
    assert field_details == {'name': 'str', 'age': 'int'}


def test_get_name_function_io(sample_project_path):
    """
    Tests that the virtual folder for 'get_name' has correct inputs/outputs.
    """
    scanner = ProjectScanner(sample_project_path)
    scanner.scan()

    manager = CodeGraphManager()
    project = manager.get_all_projects()[0]

    data = _get_virtual_folder_data(
        project, "models.user.User.get_name", "get_name_test"
    )
    
    get_name_folder = data['children'][0]
    assert get_name_folder['name'] == 'get_name'
    
    linked_func = get_name_folder.get('link_to', {})
    assert linked_func, "get_name function not linked"
    
    inputs = linked_func.get('inputs', [])
    assert len(inputs) == 0, "Inputs should be empty"
    
    outputs = linked_func.get('outputs', [])
    assert len(outputs) == 1, "Incorrect number of outputs"
    assert outputs[0]['varType'] == 'str' 