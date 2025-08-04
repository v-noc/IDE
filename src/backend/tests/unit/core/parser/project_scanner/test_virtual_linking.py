from app.core.parser.project_scanner import ProjectScanner
from app.core.manager import CodeGraphManager
import pytest
from app.db import collections
from app.core.code_elements import Function
from pprint import pprint
pytestmark = pytest.mark.usefixtures("clear_db")

def test_link_to_code_element(sample_project_path):
   scanner = ProjectScanner(sample_project_path)    
   scanner.scan()

   manager = CodeGraphManager()
   
   projects = manager.get_all_projects()
   for project in projects:
      print("Project: ", project.qname)

   assert len(projects) == 1

   project = projects[0]

   folder = project.add_virtual_folder(folder_name="register")
# #    file = folder.add_virtual_file(file_name="test.py")

   assert len(project.get_virtual_folders()) == 1, "Virtual folder was not created"

   
   function = collections.nodes.find({"node_type": "function"})
   
   new_folder = folder.create_folder_for_element(Function(function[3]))

   data = folder.get_descendant_tree()
   print("Data: ")
   pprint(data)
   # assert data["linked_element"]["id"] == function[0].id, "Linked element is not the same as the function"
   

   
  