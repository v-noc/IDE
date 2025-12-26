from typing import Dict, Any, List
from .base.node_repo import NodeRepository
from app.core.model.nodes import FileNode
from arangoasync.database import AsyncDatabase


class FileRepo(NodeRepository[FileNode]):
    def __init__(self, db: AsyncDatabase):
        super().__init__(db, "nodes", FileNode)

    async def get_all_files_snapshot(self) -> List[Dict[str, Any]]:
        """
        Returns a list of file details (path, id, checksum).
        Used for change detection.
        """

        query = """
            FOR n IN @@collection
                FILTER n.node_type == "file"
                RETURN {
                    path: n.path,
                    id: n._key,
                    checksum: n.hash
                }
        """
        cursor = await self.db.aql.execute(
            query,
            bind_vars={"@collection": self.collection_name}
        )
        return [doc async for doc in cursor]

    async def get_by_ids(self, ids: List[str]) -> Dict[str, FileNode]:
        """Fetch multiple file nodes by their IDs."""
        if not ids:
            return {}

        clean_ids = [i.split("/")[-1] if "/" in i else i for i in ids]

        query = """
            FOR n IN @@collection
                FILTER n._key IN @ids
                FILTER n.node_type == "file"
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

    async def get_by_qnames(self, qnames: List[str]) -> Dict[str, FileNode]:
        """Fetch multiple file nodes by their qualified names."""
        if not qnames:
            return {}

        query = """
            FOR n IN @@collection
                FILTER n.qname IN @qnames
                FILTER n.node_type == "file"
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
        """Batch delete multiple files by ID."""
        if not ids:
            return True

        clean_ids = [i.split("/")[-1] if "/" in i else i for i in ids]

        success = True
        for node_id in clean_ids:
            if not await self.delete(node_id):
                success = False
        return success
