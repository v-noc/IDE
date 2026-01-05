from typing import List, Dict
from app.core.repository.base.node_repo import NodeRepository
from app.core.model.nodes import FunctionNode
from arangoasync.database import AsyncDatabase


class FunctionRepo(NodeRepository[FunctionNode]):
    def __init__(self, db: AsyncDatabase):
        super().__init__(db, "nodes", FunctionNode)

    async def get_by_qnames(self, qnames: List[str]) -> Dict[str, FunctionNode]:
        """Fetch multiple function nodes by their qualified names."""
        if not qnames:
            return {}

        query = """
            FOR n IN @@collection
                FILTER n.qname IN @qnames
                FILTER n.node_type == "function"
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
        """Batch delete multiple functions by ID."""
        if not ids:
            return True
            
        clean_ids = [i.split("/")[-1] if "/" in i else i for i in ids]
        
        success = True
        for node_id in clean_ids:
            if not await self.delete(node_id):
                success = False
        return success
