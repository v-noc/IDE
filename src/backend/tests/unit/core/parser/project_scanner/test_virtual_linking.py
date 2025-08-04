from app.core.parser.project_scanner import ProjectScanner
from app.core.manager import CodeGraphManager
import pytest
from app.db import collections

pytestmark = pytest.mark.usefixtures("clear_db")

def test_link_to_code_element(sample_project_path):
   scanner = ProjectScanner(sample_project_path)    
   scanner.scan()

   manager = CodeGraphManager()
   projects = manager.get_all_projects()
   assert len(projects) == 1

   project = projects[0]

   folder = project.add_virtual_folder(folder_name="register")
#    file = folder.add_virtual_file(file_name="test.py")

   assert len(project.get_virtual_folders()) == 1, "Virtual folder was not created"

   
   function = collections.nodes.find({"node_type": "function"})
   
   folder.link_to_code_element(function[0].id)

   data = folder.to_dict()
   assert data["linked_element"]["id"] == function[0].id, "Linked element is not the same as the function"

#    assert len(folder.get_code_elements()) == 1
#    assert folder.get_code_elements()[0].key == function.key

#    assert len(function.get_virtual_folders()) == 1
#    assert function.get_virtual_folders()[0].key == folder.key

#    assert len(project.get_virtual_folders()) == 1
   