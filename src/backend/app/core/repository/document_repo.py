from .base.node_repo import NodeRepository
from app.core.model.documents import DocumentNode
from arango.database import StandardDatabase
from typing import List


class DocumentRepo(NodeRepository[DocumentNode]):
    def __init__(self, db: StandardDatabase):
        super().__init__(db, "documents", DocumentNode)

    async def node_exists(self, node_ref: str) -> bool:
        """Return True if node exists; accepts key or full ID."""
        query = """
            LET isFullId = CONTAINS(@node_ref, "/")
            LET node = isFullId
                ? DOCUMENT(@node_ref)
                : DOCUMENT(@@nodes_collection, @node_ref)
            RETURN node != null
        """
        cursor = await self.db.aql.execute(
            query,
            bind_vars={
                "@nodes_collection": "nodes",
                "node_ref": node_ref,
            },
        )
        result = await cursor.next() if cursor else None
        return bool(result)

    async def get_documents_for_node(self, node_ref: str) -> List[DocumentNode]:
        """Fetch documents for a node via one AQL; accepts key or full ID."""
        query = """
            LET isFullId = CONTAINS(@node_ref, "/")
            LET node = isFullId
                ? DOCUMENT(@node_ref)
                : DOCUMENT(@@nodes_collection, @node_ref)
            FOR doc IN (node ? DOCUMENT(node.documents) : [])
                FILTER doc != null
                RETURN doc
        """
        cursor = await self.db.aql.execute(
            query,
            bind_vars={
                "@nodes_collection": "nodes",
                "node_ref": node_ref,
            },
        )
        # Validate each document row into DocumentNode
        results = []
        async for doc in cursor:
            results.append(self._validate(doc))
        return results
