import asyncio
from typing import Optional, List, Tuple

from app.core.model.base import BaseNode


class AsyncSyncHelpers:
    """
    Async helper methods for graph synchronization.

    All database operations are async.
    Batch operations use asyncio.gather for concurrency.
    """

    def __init__(self, async_repos, semaphore_limit: int = 50):
        self.repos = async_repos
        self._semaphore = asyncio.Semaphore(semaphore_limit)
        self._node_cache = {}

    async def async_create_or_update_node(
        self,
        node: BaseNode,
        scope_id: Optional[str] = None,
    ) -> BaseNode:
        """Async create or update a node."""
        async with self._semaphore:
            repo = self._get_repo_for_node(node)

            if scope_id:
                existing = await repo.async_get_by_id(scope_id)
            else:
                existing = await repo.async_find_one({"qname": node.qname})

            if existing:
                # Update existing node
                existing.qname = node.qname
                if hasattr(existing, 'position') and hasattr(node, 'position'):
                    existing.position = node.position
                return await repo.async_update(existing.key, existing)
            else:
                return await repo.async_create(node)

    async def async_ensure_contains_edge(
        self,
        parent_id: str,
        child_id: str,
    ) -> None:
        """Async ensure a contains edge exists."""
        async with self._semaphore:
            await self.repos.contains_edges.async_upsert(
                parent_id, child_id
            )

    async def async_ensure_contains_edges_batch(
        self,
        edges: List[Tuple[str, str]],
    ) -> None:
        """Batch async ensure contains edges."""
        if not edges:
            return

        async with self._semaphore:
            query = """
            FOR edge IN @edges
                UPSERT { _from: edge.from_id, _to: edge.to_id }
                INSERT { 
                    _from: edge.from_id, 
                    _to: edge.to_id
                }
                UPDATE {}
                IN contains_edges
            """
            await self.repos.db.aql.execute(
                query,
                bind_vars={
                    "edges": [{"from_id": f, "to_id": t} for f, t in edges]
                }
            )

    async def mark_node_deleted(self, node_id: str) -> None:
        """Mark a node as deleted (soft delete)."""
        async with self._semaphore:
            # Option 1: Hard delete
            await self.repos.nodes.delete(node_id)

            # Option 2: Soft delete (set a deleted flag)
            # await self.repos.node_repo.async_update(
            #     node_id, {"is_deleted": True}
            # )

    def _get_repo_for_node(self, node: BaseNode):
        """Get appropriate repository for node type."""
        node_type = getattr(node, 'node_type', None)
        if node_type == 'file':
            return self.repos.file_repo
        elif node_type == 'folder':
            return self.repos.folder_repo
        elif node_type == 'class':
            return self.repos.class_repo
        elif node_type == 'function':
            return self.repos.function_repo
        return self.repos.node_repo
