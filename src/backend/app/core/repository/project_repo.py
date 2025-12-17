

import asyncio

from app.core.model.nodes import ProjectNode
from app.core.repository.base.node_repo import NodeRepository
from arango.database import StandardDatabase


class ProjectRepo(NodeRepository[ProjectNode]):
    """Repository for project collections."""

    def __init__(self, db: StandardDatabase):
        super().__init__(db, "nodes", ProjectNode)

    async def get_all_projects(self):
        return await self.find({"node_type": "project"})

    async def delete(self, key: str) -> bool:
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
            vertex_ids_cursor = await self.db.aql.execute(
                collect_vertices_query,
                bind_vars={
                    "start_node_id": start_node_id,
                    "@contains_collection": "contains_edges",
                },
            )
            vertex_ids_lists = []
            async for doc in vertex_ids_cursor:
                vertex_ids_lists.append(doc)
            vertex_ids = vertex_ids_lists[0] if vertex_ids_lists else []

            if not vertex_ids:
                # If nothing is found, still attempt to delete the
                # root project doc to return a meaningful result.
                collection = await self.get_collection()
                await collection.delete(key)
                return True

            # 2) Resolve all edge collections dynamically
            edge_collections = await self._get_edge_collections()

            # 3) For each edge collection, bulk-remove edges connected
            #    to any of the collected vertices
            remove_edges_query = (
                """
                FOR e IN @@edge_collection
                  FILTER e._from IN @vertexIds OR e._to IN @vertexIds
                  REMOVE e IN @@edge_collection
                """
            )
            delete_edge_tasks = [
                self.db.aql.execute(
                    remove_edges_query,
                    bind_vars={
                        "@edge_collection": edge_col,
                        "vertexIds": vertex_ids,
                    },
                )
                for edge_col in edge_collections
            ]
            await asyncio.gather(*delete_edge_tasks, return_exceptions=True)

            # 4) Bulk-remove all vertices (convert _id -> _key)
            remove_vertices_query = (
                """
                FOR vid IN @vertexIds
                  LET key = SPLIT(vid, "/")[1]
                  REMOVE { _key: key } IN @@vertex_collection
                """
            )
            await self.db.aql.execute(
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
