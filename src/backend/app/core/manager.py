"""
The CodeGraphManager: the main entry point for the Domain API.
"""
from typing import List
from .project import Project
from ..models import node, properties
from ..db import collections as db


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

    def get_all_projects(self) -> List[node.ProjectNode]:
        """
        Retrieves all projects from the database.
        """
        return db.nodes.find({"node_type": "project"})

    def delete_project(self, project_key: str) -> bool:
        """
        Deletes a project from the database.
        """
        return db.nodes.delete(project_key)

    def update_project(self, project_key: str, name: str, path: str) -> Project | None:
        """
        Updates a project in the database.
        """
        project_node = self.get_project(project_key)
        if not project_node:
            return None
        
        project_node.name = name
        project_node.properties.path = path
        
        db.nodes.update(project_node)
        return Project(project_node)
