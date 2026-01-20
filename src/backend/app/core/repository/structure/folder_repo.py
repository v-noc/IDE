from typing import Dict, Any, List
from .base.node_repo import NodeRepository
from app.core.model.nodes import FolderNode
from arangoasync.database import AsyncDatabase


class FolderRepo(NodeRepository[FolderNode]):
    def __init__(self, db: AsyncDatabase):
        super().__init__(db, "nodes", FolderNode)

    async def get_project_folders(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Returns a list of folder details (path, id) belonging to the specific project.
        """
        query = """
            FOR v, e, p IN 1..100 OUTBOUND @project_id @@contains_collection
                OPTIONS { order: "bfs", uniqueVertices: "global" }
                FILTER v.node_type == "folder"
                RETURN {
                    path: v.path,
                    id: v._key
                }
        """
        try:
            cursor = await self.db.aql.execute(
                query,
                bind_vars={
                    "project_id": project_id,
                    "@contains_collection": "contains_edges"
                }
            )
            return [doc async for doc in cursor]
        except Exception as e:
            print(f"Failed to get project folders snapshot: {e}")
            return []


