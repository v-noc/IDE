from typing import Dict, Any, List
from ..base.base_node_repo import NodeRepository
from app.core.model.nodes import FileNode
from arangoasync.database import AsyncDatabase


class FileRepo(NodeRepository[FileNode]):
    def __init__(self, db: AsyncDatabase):
        super().__init__(db, "nodes", FileNode)

    async def get_project_files(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Returns a list of file details (path, id, checksum) belonging to the specific project.
        Uses graph traversal to ensure we only get nodes connected to this project.
        """
        query = """
            FOR v, e, p IN 1..100 OUTBOUND @project_id @@contains_collection
                OPTIONS { order: "bfs", uniqueVertices: "global" }
                FILTER v.node_type == "file"
                // Optional: Double check path just in case, but graph logic is primary
                RETURN {
                    path: v.path,
                    id: v._key,
                    checksum: v.hash
                }
        """
        cursor = await self.db.aql.execute(
            query,
            bind_vars={
                "project_id": project_id,
                "@contains_collection": "contains_edges"
            }
        )
        return [doc async for doc in cursor]


