

from app.core.model.nodes import ProjectNode
from app.core.repository.base.node_repo import NodeRepository
from arango.database import StandardDatabase


class ProjectRepo(NodeRepository[ProjectNode]):
    """Repository for project collections."""

    def __init__(self, db: StandardDatabase):
        super().__init__(db, "nodes", ProjectNode)

    def get_all_projects(self):
        return self.find({"node_type": "project"})

    def delete(self, key: str) -> bool:
        """Deletes a project and all its children (cascade)."""
        try:
            # Build the start vertex id, e.g. "nodes/<key>"
            start_node_id = f"{self.collection_name}/{key}"

            # 1) Collect all descendant vertex ids
            #    (including the project itself)
            collect_vertices_query = (
                """
                LET vertexIds = APPEND(
                  [@start_node_id],
                  FOR v IN 1..50 OUTBOUND @start_node_id @@contains_collection
                    RETURN v._id
                )
                RETURN UNIQUE(vertexIds)
                """
            )
            vertex_ids_cursor = self.db.aql.execute(
                collect_vertices_query,
                bind_vars={
                    "start_node_id": start_node_id,
                    "@contains_collection": "contains_edges",
                },
            )
            vertex_ids_lists = list(vertex_ids_cursor)
            vertex_ids = vertex_ids_lists[0] if vertex_ids_lists else []

            if not vertex_ids:
                # If nothing is found, still attempt to delete the
                # root project doc to return a meaningful result.
                self.collection.delete(key)
                return True

            # 2) Resolve all edge collections dynamically
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

            # 3) For each edge collection, bulk-remove edges connected
            #    to any of the collected vertices
            remove_edges_query = (
                """
                FOR e IN @@edge_collection
                  FILTER e._from IN @vertexIds OR e._to IN @vertexIds
                  REMOVE e IN @@edge_collection
                """
            )
            for edge_col in edge_collections:
                self.db.aql.execute(
                    remove_edges_query,
                    bind_vars={
                        "@edge_collection": edge_col,
                        "vertexIds": vertex_ids,
                    },
                )

            # 4) Bulk-remove all vertices (convert _id -> _key)
            remove_vertices_query = (
                """
                FOR vid IN @vertexIds
                  LET key = SPLIT(vid, "/")[1]
                  REMOVE { _key: key } IN @@vertex_collection
                """
            )
            self.db.aql.execute(
                remove_vertices_query,
                bind_vars={
                    "vertexIds": vertex_ids,
                    "@vertex_collection": self.collection_name,
                },
            )

            return True
        except Exception as e:
            print(f"Cascade project delete failed: {e}")
            return False
