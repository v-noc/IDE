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

    async def get_by_ids(self, ids: List[str]) -> Dict[str, FolderNode]:
        """Fetch multiple folder nodes by their IDs."""
        if not ids:
            return {}

        # Clean IDs (remove collection prefix if present)
        clean_ids = [i.split("/")[-1] if "/" in i else i for i in ids]

        query = """
            FOR n IN @@collection
                FILTER n._key IN @ids
                FILTER n.node_type == "folder"
                RETURN n
        """
        cursor = await self.db.aql.execute(
            query,
            bind_vars={"@collection": self.collection_name, "ids": clean_ids}
        )
        results = {}
        async for doc in cursor:
            node = self._validate(doc)
            results[node.key] = node
        return results

    async def get_by_qnames(self, qnames: List[str]) -> Dict[str, FolderNode]:
        """Fetch multiple folder nodes by their qualified names."""
        if not qnames:
            return {}

        query = """
            FOR n IN @@collection
                FILTER n.qname IN @qnames
                FILTER n.node_type == "folder"
                RETURN n
        """
        cursor = await self.db.aql.execute(
            query,
            bind_vars={"@collection": self.collection_name, "qnames": qnames}
        )
        results = {}
        async for doc in cursor:
            node = self._validate(doc)
            results[node.qname] = node
        return results

    async def delete_batch(self, ids: List[str]) -> bool:
        """Batch delete multiple folders by ID."""
        if not ids:
            return True

        clean_ids = [i.split("/")[-1] if "/" in i else i for i in ids]

        # We should use the generic delete strategy (edges first) but batching it is hard with
        # generic edge deletion logic.
        # For now, let's just delete the nodes.
        # CAUTION: This leaves dangling edges if not handled.
        # But NodeRepository.delete() handles edges.
        # We can loop calling self.delete() or implement a batch version.
        # Given ArangoDB, it's better to delete edges in batch too.

        # Implementation: Simple loop for safety/correctness first
        # Optimizing this requires batch-edge-finding.

        success = True
        for node_id in clean_ids:
            if not await self.delete(node_id):
                success = False
        return success
