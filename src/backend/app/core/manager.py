"""
The CodeGraphManager: the main entry point for the Domain API.
"""
from typing import List, Optional
from .project import Project
from ..models import node, properties
from ..db import collections as db
from .virtual_folder import VirtualFolder
from .virtual_file import VirtualFile

class CodeGraphManager:
    """
    Provides high-level methods to create and load projects, serving as the
    entry point for all domain-centric graph operations.
    """
    def create_project(self, name: str, path: str) -> Project:
        """
        Creates a new project node, saves it to the database, and returns the
        node model.
        """
        project_node_model = node.ProjectNode(
            name=name,
            qname=name,
            node_type="project",
            properties=properties.ProjectProperties(path=path)
        )
        return Project(db.nodes.create(project_node_model))

    def get_project(self, project_key: str) -> Project | None:
        """
        Loads an existing project from the database by its key.
        """
        project_node = db.nodes.get(project_key)
        if not project_node or not isinstance(project_node, node.ProjectNode):
            return None
        return Project(project_node)

    def get_all_projects(self) -> List[Project]:
        """
        Retrieves all projects from the database.
        """
        return [Project(project_node) for project_node in db.nodes.find({"node_type": "project"})]

    def delete_project(self, project_key: str) -> bool:
        """
        Deletes a project from the database.
        """
        return db.nodes.delete(project_key)


    def get_virtual_folder(self, folder_key: str) -> VirtualFolder | None:
        """
        Loads an existing virtual folder from the database by its key.
        """
        virtual_folder_node = db.nodes.get(folder_key)
        if not virtual_folder_node or not isinstance(virtual_folder_node, node.VirtualFolderNode):
            return None
        return VirtualFolder(virtual_folder_node)
    
    def create_virtual_folder(self, project_id: str, folder_name: str, description: Optional[str] = None, parent_id: Optional[str] = None) -> VirtualFolder:
        """
        Creates a new virtual folder in the project.
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        if parent_id:
            parent_folder = self.get_virtual_folder(parent_id)
            if not parent_folder:
                raise ValueError(f"Parent folder with ID {parent_id} not found")
            return parent_folder.add_virtual_folder(folder_name, description)
        else:
            return project.add_virtual_folder(folder_name, description)
        
    def create_virtual_file(self, project_id: str, file_name: str, description: Optional[str] = None, parent_id: Optional[str] = None) -> VirtualFile:
        """
        Creates a new virtual file in the project.
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        if parent_id:
            parent_folder = self.get_virtual_folder(parent_id) 
            if not parent_folder:
                raise ValueError(f"Parent folder with ID {parent_id} not found")
            return parent_folder.add_virtual_file(file_name, description)
        else:
            raise ValueError("Parent folder ID is required for virtual file creation")