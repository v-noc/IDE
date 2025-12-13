from typing import Any, Dict, List, Optional, TypeVar

from arango.exceptions import DocumentDeleteError, DocumentGetError
from pydantic import BaseModel

from app.core.model import AllNodes
from app.core.model.nodes import ProjectNode

from .base_collection import BaseRepository

T = TypeVar("T", bound=BaseModel)


class NodeRepository(BaseRepository[T]):
    """Repository for node collections."""

    def delete(self, key: str) -> bool:
        """Deletes a node and all edges connected to it."""
        node_id = f"{self.collection_name}/{key}"

        try:
            edge_collections = [
                c["name"]
                for c in self.db.collections()
                if not c.get("system")
                and self.db.collection(c["name"]).properties().get("edge")
            ]
        except Exception as e:
            print(f"Failed to retrieve edge collections: {e}")
            return False

        try:
            for ec_name in edge_collections:
                self.db.aql.execute(
                    (
                        """
                        FOR e IN @@collection
                            FILTER e._from == @node_id OR e._to == @node_id
                            REMOVE e IN @@collection
                        """
                    ),
                    bind_vars={"@collection": ec_name, "node_id": node_id},
                )

            self.collection.delete(key)
            return True
        except (DocumentDeleteError, DocumentGetError):
            return False
        except Exception as e:
            print(f"An unexpected error occurred during node deletion: {e}")
            return False

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
        results = list(cursor)
        if results:
            return results[0]
        return None

    def get_parent_project(self, node_id: str) -> Optional[ProjectNode]:
        """Finds the structural parent of a node via the 'contains' edge."""
        query = """
            FOR v IN 1..100 INBOUND @start_node_id @@contains_collection
                OPTIONS { order: "bfs" }
                FILTER v.node_type == "project"
                LIMIT 1
                RETURN v
            """
        bind_vars = {
            "start_node_id": node_id,
            "@contains_collection": "contains_edges",
        }
        # Note: This returns raw dicts, not Pydantic models directly,
        # because the structure is custom ("vertex", "parent_id").
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        results = list(cursor)
        if results:
            return results[0]
        return None

    def get_containment_tree(
        self,
        start_node_id: str,
        depth: int | str = 50,
        exclude_types: List[str] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes a graph traversal to get a full descendant tree.
        Returns a list of dictionaries, each containing the vertex and its
        parent's ID, perfect for rebuilding a tree structure.
        """
        # For MVP, use a large fixed depth for unbounded requests instead of
        # '1..' syntax
        max_depth = 50 if depth == "*" else depth

        # AQL's "p.vertices[-2]" gets the direct parent. We sometimes need to
        # skip virtual nodes (e.g., group) and attach children to the nearest
        # non-excluded ancestor while still traversing through excluded nodes.
        query = """
    // 1. Setup Start Node
    LET start_node = DOCUMENT(@start_node_id)
    LET start_ver = start_node.current_version != null ? start_node.current_version : 0

    FOR v, e, p IN 1..@max_depth OUTBOUND @start_node_id
        @@contains_collection
        
        // --- FIX IS HERE ---
        // PRUNE must be here (before loop body LETs).
        // We must inline the logic because 'immediate_parent' is not defined yet.
        PRUNE (
            (v.current_version != null ? v.current_version : 0) 
            < 
            (LENGTH(p.vertices) >= 2 
                ? (p.vertices[-2].current_version != null ? p.vertices[-2].current_version : 0)
                : start_ver
            )
        )
        
        OPTIONS { order: "bfs", uniqueVertices: "global" }

        // 2. GET IMMEDIATE PARENT (For Output/Calculations)
        LET immediate_parent = LENGTH(p.vertices) >= 2 ? p.vertices[-2] : start_node
        LET imm_parent_ver = immediate_parent.current_version != null ? immediate_parent.current_version : 0
        
        // 3. (Optional) Re-check Edge Version if needed for specific logic
        FILTER (e.version != null ? e.version : 0) >= imm_parent_ver

        // 4. OUTPUT CALCULATIONS
        LET parent_candidates = (
            FOR i IN 2..LENGTH(p.vertices)
                LET candidate = p.vertices[LENGTH(p.vertices) - i]
                FILTER candidate.node_type NOT IN @exclude_types
                LIMIT 1
                RETURN candidate._id
        )

        // 5. EXCLUDE TYPES FROM OUTPUT
        FILTER v.node_type NOT IN @exclude_types

        // 6. TARGET LOGIC
        LET target_node = (
            FOR target IN 1..1 OUTBOUND v @@targets_collection
                LIMIT 1
                RETURN target
        )

        RETURN {
            "vertex": v,
            "parent_id": FIRST(parent_candidates),
            "target": FIRST(target_node)
        }
"""
        bind_vars = {
            "start_node_id": start_node_id,
            "@contains_collection": "contains_edges",
            "@targets_collection": "targets_edges",
            "max_depth": max_depth,
            "exclude_types": exclude_types or [],
        }
        # Note: This returns raw dicts, not Pydantic models directly,
        # because the structure is custom ("vertex", "parent_id").
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        b = list(cursor)
        return b

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
