"""
The main GraphBuilder service for constructing the ArangoDB graph.
"""
from ..db.service import DatabaseService
from ..models.project import Project
from .scanner import ProjectScanner
from .factories import NodeFactory, EdgeFactory

class GraphBuilder:
    """
    Orchestrates the scanning of a project and the construction of its
    corresponding graph in ArangoDB.
    """
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
        self.scanner = ProjectScanner()
        self.node_factory = NodeFactory()
        self.edge_factory = EdgeFactory()
        # A map to keep track of created nodes to avoid duplicates
        # and easily create edges. Key is the qualified name (qname).
        self.known_nodes = {}

    def build_graph_for_project(self, project: Project):
        """
        Scans the project path and builds the entire graph.
        """
        # 1. Create the root project node
        project_node = self.node_factory.create_project_node(project.name, project.path)
        created_project_node = self.db.nodes.create(project_node)
        self.known_nodes[created_project_node.qname] = created_project_node.key

        # 2. Scan the project directory
        for item_type, data in self.scanner.scan(project.path):
            if item_type == "folder":
                self._process_folder(data, created_project_node)
            elif item_type == "file":
                self._process_file(data, created_project_node)
            elif item_type == "ast":
                self._process_ast(data)

    def _get_or_create_node(self, node_creation_func, *args, **kwargs) -> str:
        """Helper to avoid creating duplicate nodes."""
        temp_node = node_creation_func(*args, **kwargs)
        qname = temp_node.qname
        
        if qname in self.known_nodes:
            return self.known_nodes[qname]
            
        created_node = self.db.nodes.create(temp_node)
        self.known_nodes[qname] = created_node.key
        return created_node.key

    def _process_folder(self, data: dict, project_node: Project):
        folder_path = data["path"]
        parent_path = data["parent"]
        
        folder_key = self._get_or_create_node(self.node_factory.create_folder_node, folder_path)
        
        # Link to parent (either another folder or the project root)
        parent_key = self.known_nodes.get(parent_path)
        if not parent_key:
             # If parent isn't a folder, it must be the project root
            parent_key = self.known_nodes.get(project_node.name)

        if parent_key:
            # We don't have position for folder contains folder, so use default
            from ..models.node import NodePosition
            pos = NodePosition(line_no=0, col_offset=0, end_line_no=0, end_col_offset=0)
            contains_edge = self.edge_factory.create_contains_edge(f"nodes/{parent_key}", f"nodes/{folder_key}", pos)
            self.db.contains.create(contains_edge.from_doc_id, contains_edge.to_doc_id, contains_edge)

    def _process_file(self, data: dict, project_node: Project):
        file_path = data["path"]
        parent_path = data["parent"]

        file_key = self._get_or_create_node(self.node_factory.create_file_node, file_path)
        
        # Link to parent folder
        parent_key = self.known_nodes.get(parent_path)
        if parent_key:
            from ..models.node import NodePosition
            pos = NodePosition(line_no=0, col_offset=0, end_line_no=0, end_col_offset=0)
            contains_edge = self.edge_factory.create_contains_edge(f"nodes/{parent_key}", f"nodes/{file_key}", pos)
            self.db.contains.create(contains_edge.from_doc_id, contains_edge.to_doc_id, contains_edge)

    def _process_ast(self, data: dict):
        file_path = data["path"]
        results = data["results"]
        file_key = self.known_nodes.get(file_path)

        if not file_key:
            return # Should not happen if file was processed first

        # Process functions, classes, etc., found in the file
        for func_data in results.get("functions", []):
            func_key = self._get_or_create_node(self.node_factory.create_function_node, **func_data)
            contains_edge = self.edge_factory.create_contains_edge(f"nodes/{file_key}", f"nodes/{func_key}", func_data['position'])
            self.db.contains.create(contains_edge.from_doc_id, contains_edge.to_doc_id, contains_edge)

        for class_data in results.get("classes", []):
            class_key = self._get_or_create_node(self.node_factory.create_class_node, **class_data)
            contains_edge = self.edge_factory.create_contains_edge(f"nodes/{file_key}", f"nodes/{class_key}", class_data['position'])
            self.db.contains.create(contains_edge.from_doc_id, contains_edge.to_doc_id, contains_edge)
        
        # Here you would add more logic to process calls, imports, etc.
        # and create CallEdge and ImportEdge connections. This requires a more
        # sophisticated way to resolve what a call name refers to, which is
        # beyond a simple AST scan.
