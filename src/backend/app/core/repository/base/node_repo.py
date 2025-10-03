from typing import Any, Optional, List, Dict

from app.core.model import AllNodes
from .base_collection import BaseRepository
from pydantic import BaseModel
from typing import TypeVar


T = TypeVar('T', bound=BaseModel)


class NodeRepository(BaseRepository[T]):
    """Repository for node collections."""

    def get_parent(self, node_id: str) -> Optional[AllNodes]:
        """Finds the structural parent of a node via the 'contains' edge."""
        query = """
        FOR v, e, p IN 1..1 INBOUND @start_node_id @@contains_collection
            OPTIONS { order: "bfs" }
            RETURN {
                "vertex": v,
                "parent_id": p.vertices[-2]._id
            }
        """
        bind_vars = {
            "start_node_id": node_id,
            "@contains_collection": "contains_edges",

        }
        # Note: This returns raw dicts, not Pydantic models directly,
        # because the structure is custom ("vertex", "parent_id").
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        return list(cursor)

    def get_containment_tree(
        self, start_node_id: str, max_depth: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Executes a graph traversal to get a full descendant tree.
        Returns a list of dictionaries, each containing the vertex and its
        parent's ID, perfect for rebuilding a tree structure.
        """
        # AQL's "p.vertices[-2]" is a clever way to get the parent in a path.
        query = """
        FOR v, e, p IN 1..@max_depth OUTBOUND @start_node_id 
            @@contains_collection
            OPTIONS { order: "bfs" }
            // Use a LET statement to conditionally find the target
            LET target_node = (
                // This subquery only runs IF v is a call node
                FOR target IN 1..1 OUTBOUND v @@targets_collection
                    LIMIT 1
                    RETURN target
            )
            RETURN {
                "vertex": v,
                "parent_id": p.vertices[-2]._id,
                "target": FIRST(target_node)
            }
        """
        bind_vars = {
            "start_node_id": start_node_id,
            "@contains_collection": "contains_edges",
            "@targets_collection": "targets_edges",
            "max_depth": max_depth,
        }
        # Note: This returns raw dicts, not Pydantic models directly,
        # because the structure is custom ("vertex", "parent_id").
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        return list(cursor)

    def get_nearest_file_and_project(self, node_id: str) -> Dict[str, Any]:
        """Return nearest file and project ancestors in one traversal.

        Performs a BFS INBOUND traversal on contains_edges starting from
        node_id. Selects first encountered file and project nodes.

        Returns a dict with keys file and project whose values are the raw
        vertex documents or None if not found.
        """
        query = """
        LET ancestors = (
          FOR v IN 1..50 INBOUND @start_node_id @@contains_collection
            OPTIONS { order: "bfs" }
            RETURN v
        )
        RETURN {
          file: FIRST(
            FOR a IN ancestors
              FILTER a.node_type == "file"
              RETURN a
          ),
          project: FIRST(
            FOR a IN ancestors
              FILTER a.node_type == "project"
              RETURN a
          )
        }
        """
        bind_vars = {
            "start_node_id": node_id,
            "@contains_collection": "contains_edges",
        }
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        results = list(cursor)
        if results:
            return results[0]
        return {"file": None, "project": None}

    def find_by_qname(self, qname: str) -> Optional[T]:
        return self.find_one({"qname": qname})

    def find_by_type(self, node_type: str) -> List[T]:
        return self.find({"node_type": node_type})
