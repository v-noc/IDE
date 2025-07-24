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
        Creates a new project node, saves it to the database, and returns a
        hydrated Project domain object.
        """
        # 1. Create the ProjectNode model
        project_node_model = node.ProjectNode(
            name=name,
            qname=name,  # The qualified name for a project is just its name
            node_type="project",
            properties=properties.ProjectProperties(path=path)
        )

        # 2. Save to the 'nodes' collection
        created_node = db.nodes.create(project_node_model)

        # 3. Return the hydrated domain object
        return Project(created_node)

    def load_project(self, project_key: str) -> Project:
        """
        Loads an existing project from the database by its key and returns a
        hydrated Project domain object.
        """
        # 1. Load the project node from the 'nodes' collection
        project_node = db.nodes.get(project_key)
        if not project_node:
            raise ValueError(f"Project with key '{project_key}' not found.")
        
        if not isinstance(project_node, node.ProjectNode):
            raise TypeError(f"Document with key '{project_key}' is not a ProjectNode.")

        # 2. Return the hydrated domain object
        return Project(project_node)

    def get_all_projects(self) -> List[Project]:
        """
        Retrieves all projects from the database.
        """
        project_nodes = db.nodes.find({"node_type": "project"})
        return [Project(node) for node in project_nodes]

# A default instance for use in API endpoints
code_graph_manager = CodeGraphManager()