"""
The CodeGraphManager: the main entry point for the Domain API.
"""
from ..db.service import DatabaseService, db_service
from ..models.project import Project as ProjectModel
from .project import Project
from ..graph.factories import NodeFactory

class CodeGraphManager:
    """
    Provides high-level methods to create and load projects, serving as the
    entry point for all domain-centric graph operations.
    """
    def __init__(self, db: DatabaseService):
        self.db = db
        self.node_factory = NodeFactory()

    def create_project(self, name: str, path: str, description: str = "") -> Project:
        """
        Creates a new project, saves it to the database, and returns a
        hydrated Project domain object.
        """
        # 1. Create the Project model
        project_model = ProjectModel(name=name, description=description, path=path)
        
        # 2. Save to DB
        created_project_doc = self.db.projects.create(project_model)
        
        # 3. Create the root Project Node in the 'nodes' collection
        project_node = self.node_factory.create_project_node(name, path)
        created_node = self.db.nodes.create(project_node)

        # 4. Return the hydrated domain object
        return Project(
            project_model=created_project_doc, 
            node_model=created_node, 
            db_service=self.db
        )

    def load_project(self, project_key: str) -> Project:
        """
        Loads an existing project from the database and returns a hydrated
        Project domain object.
        """
        # 1. Load the project document
        project_doc = self.db.projects.get(project_key)
        if not project_doc:
            raise ValueError(f"Project with key '{project_key}' not found.")
            
        # 2. Find the corresponding root node in the 'nodes' collection
        # This assumes the qualified name of the project node is its name.
        project_node_docs = self.db.nodes.find({"qname": project_doc.name, "node_type": "project"})
        if not project_node_docs:
            raise ValueError(f"Root node for project '{project_key}' not found.")
        
        project_node = project_node_docs[0]

        # 3. Return the hydrated domain object
        return Project(
            project_model=project_doc,
            node_model=project_node,
            db_service=self.db
        )

# A default instance for use in API endpoints
code_graph_manager = CodeGraphManager(db_service)
