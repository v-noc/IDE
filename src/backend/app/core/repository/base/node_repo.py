from typing import Any, Optional, List, Dict

from app.core.model import AllNodes
from .base_collection import BaseRepository
from pydantic import BaseModel
from typing import TypeVar
from arango.exceptions import DocumentDeleteError, DocumentGetError


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
                OPTIONS { order: "bfs", uniqueVertices: "global" }

                // 2. GET IMMEDIATE PARENT (The node strictly above 'v' in the path)
                // If we are at depth 1, the parent is the start_node.
                // If we are deeper, it is the second-to-last vertex in the path.
                LET immediate_parent = LENGTH(p.vertices) >= 2 ? p.vertices[-2] : start_node
                
                // 3. GET VERSIONS
                LET imm_parent_ver = immediate_parent.current_version != null ? immediate_parent.current_version : 0
                LET v_ver = v.current_version != null ? v.current_version : 0

         

                // 5. FILTER CURRENT NODE
                // We also hide this specific node from results.
                FILTER v_ver >= imm_parent_ver
                
                // (Optional) If edges act as the "pointer" update, check edge version too
                FILTER (e.version != null ? e.version : 0) >= imm_parent_ver

                // 6. OUTPUT CALCULATIONS 
                // Now that we know the PATH is valid, we calculate who the "Logical Parent" is
                // (This is purely for your JSON output, NOT for validity checks)
                LET parent_candidates = (
                    FOR i IN 2..LENGTH(p.vertices)
                        LET candidate = p.vertices[LENGTH(p.vertices) - i]
                        FILTER candidate.node_type NOT IN @exclude_types
                        LIMIT 1
                        RETURN candidate._id
                )

                // 7. EXCLUDE TYPES FROM OUTPUT (But keep traversing through them if valid)
                FILTER v.node_type NOT IN @exclude_types

                // 8. TARGET LOGIC (Unchanged)
                LET target_node = (
                    FOR target IN 1..1 OUTBOUND v @@targets_collection
                        LIMIT 1
                        RETURN target
                )

                RETURN {
                    "vertex": v,
                    "parent_id": FIRST(parent_candidates), // For UI/Structure
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
