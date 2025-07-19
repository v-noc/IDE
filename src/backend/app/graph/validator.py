"""
Validates the integrity of the ArangoDB graph.
"""
from ..db.service import DatabaseService

class GraphValidator:
    """
    Performs validation checks on the graph for a given project.
    """
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
        self.aql = self.db.db.aql

    def validate_project_graph(self, project_key: str) -> dict:
        """
        Runs all validation checks and returns a report.
        """
        report = {
            "orphaned_nodes": self._find_orphaned_nodes(project_key),
            "invalid_call_edges": self._find_invalid_call_edges(),
        }
        return report

    def _find_orphaned_nodes(self, project_key: str) -> list:
        """
        Finds nodes that are not the project root and have no incoming
        'belongs_to' or 'contains' edges.
        """
        query = """
        FOR node IN nodes
          FILTER node.node_type != 'project'
          LET incoming_edges = (
              FOR edge IN UNION(contains, belongs_to)
                  FILTER edge._to == node._id
                  LIMIT 1
                  RETURN 1
          )
          FILTER LENGTH(incoming_edges) == 0
          RETURN { _key: node._key, name: node.name, type: node.node_type }
        """
        cursor = self.aql.execute(query)
        return [doc for doc in cursor]

    def _find_invalid_call_edges(self) -> list:
        """
        Finds 'calls' edges that do not originate from a function or class.
        """
        query = """
        FOR call_edge IN calls
          LET from_node = DOCUMENT(call_edge._from)
          FILTER from_node.node_type NOT IN ['function', 'class']
          RETURN {
              edge_key: call_edge._key,
              from_node: { _key: from_node._key, name: from_node.name, type: from_node.node_type }
          }
        """
        cursor = self.aql.execute(query)
        return [doc for doc in cursor]
