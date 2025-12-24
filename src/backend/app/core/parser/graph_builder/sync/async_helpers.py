import asyncio
from typing import Literal, Optional, List, Tuple

from app.core.model.base import BaseNode
from app.core.parser.scope_manager.models import ScopeModel, ScopeType
from app.core.parser.graph_builder.sync.mappers import map_scope_to_position
from app.core.model.nodes import ContainerNode


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

    async def async_move_node(
        self,
        node_id: str,
        old_parent_id: str,
        new_parent_id: str,
    ) -> None:
        """Async move a node."""
        if old_parent_id:
            # Remove old edge
            await self.repos.contains_edges.db.aql.execute("""
                FOR e IN contains_edges
                    FILTER e._to == @node_id
                    REMOVE e IN contains_edges
            """, bind_vars={"node_id": node_id})

        # Create new edge
        await self.async_ensure_contains_edge(new_parent_id, node_id)

    async def async_update_node_properties(self, node: BaseNode, scope: ScopeModel) -> BaseNode:
        """Async update a node's properties."""
        async with self._semaphore:

            repo = self._get_repo_for_node(node)
            node.qname = scope.qname
            node.name = scope.name
            if hasattr(node, 'position') and hasattr(scope, 'position'):
                node.position = map_scope_to_position(scope)
            return await repo.update(node.key, node)

    async def async_create_node(self, node: BaseNode) -> BaseNode:
        """Async create a node."""
        async with self._semaphore:
            repo = self._get_repo_for_node(node)
            return await repo.create(node)

    async def async_get_node_by_id(self, node_id: str) -> Optional[BaseNode]:
        """Async get a node by its ID."""
        async with self._semaphore:
            return await self.repos.nodes.get_by_id(node_id)

    async def async_get_parent_id(self, node_id: str) -> Optional[str]:
        """Async get a node's parent ID."""
        async with self._semaphore:
            parent = await self.repos.nodes.get_parent(node_id)
            if parent:
                return parent.get("parent_id")
            return None

    async def async_get_children(self, node_id: str, node_types: List[str] = []) -> List[BaseNode]:
        """Async get a node's children IDs."""
        async with self._semaphore:
            children = await self.repos.nodes.get_children(node_id)
            if children:
                return [child for child in children if child.get("node_type") in node_types]
            return []

    async def async_create_or_update_node(
        self,
        node: BaseNode,
        scope_id: Optional[str] = None,
    ) -> BaseNode:
        """Async create or update a node."""
        async with self._semaphore:
            repo = self._get_repo_for_node(node)

            if scope_id:
                existing = await repo.get_by_id(scope_id)
            else:
                existing = await repo.find_one({"qname": node.qname})

            if existing:
                # Update existing node
                existing.qname = node.qname
                if hasattr(existing, 'position') and hasattr(node, 'position'):
                    existing.position = node.position
                return await repo.update(existing.key, existing)
            else:
                return await repo.create(node)

    async def async_mark_node_status(self, node: ContainerNode, status: Literal["active", "orphaned", "deleted"], reason: Optional[str] = None) -> None:
        """Async mark a node's status."""
        async with self._semaphore:
            node = ContainerNode(**node)
            node.status = status
            node.orphan_reason = reason
            return await self.repos.nodes.update(node.key, node)

    async def async_ensure_contains_edge(
        self,
        parent_id: str,
        child_id: str,
    ) -> None:
        """Async ensure a contains edge exists."""
        async with self._semaphore:
            try:

                query = """
                    UPSERT { _from: @from_id, _to: @to_id }
                    INSERT { 
                        _from: @from_id, 
                        _to: @to_id, 
                        contain_type: CONCAT(DOCUMENT(@from_id).node_type, "_to_", DOCUMENT(@to_id).node_type)
                    }
                    UPDATE {}
                    IN contains_edges
                """
                # Note: DOCUMENT() function allows us to get the node types inside the query!

                bind_vars = {
                    "from_id": parent_id,
                    "to_id": child_id,
                }
                await self.repos.contains_edges.db.aql.execute(
                    query, bind_vars=bind_vars)

            except Exception as e:
                pass
                # logger.error(
                #     f"Error ensuring contains edge {parent_id} -> "
                #     f"{child_id}: {e}"
                # )

    async def async_ensure_contains_edges_batch(
        self,
        edges: List[Tuple[str, str]],
    ) -> None:
        """Batch async ensure contains edges."""
        if not edges:
            return
        try:
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

                await self.repos.contains_edges.db.aql.execute(
                    query,
                    bind_vars={
                        "edges": [{"from_id": f, "to_id": t} for f, t in edges]
                    }
                )
        except Exception as e:
            print(f"Error ensuring contains edges batch: {e}")
            # logger.error(
            #     f"Error ensuring contains edges batch: {e}"
            # )

    async def async_get_graph_node_for_scope(
        self,
        scope: ScopeModel,
    ) -> Optional[BaseNode]:
        """
        Resolve graph node for scope with caching.
        """
        if scope.id in self._node_cache:
            return self._node_cache[scope.id]

        async with self._semaphore:
            node = None
            if scope.type == ScopeType.FILE:
                node = await self.repos.file_repo.find_one(
                    {"qname": scope.qname}
                )
            elif scope.type == ScopeType.CLASS:
                node = await self.repos.class_repo.find_one(
                    {"qname": scope.qname}
                )
            elif scope.type == ScopeType.FUNCTION:
                node = await self.repos.function_repo.find_one(
                    {"qname": scope.qname}
                )
            elif scope.type == ScopeType.FOLDER:
                node = await self.repos.folder_repo.find_one(
                    {"qname": scope.qname}
                )

            if node:
                self._node_cache[scope.id] = node
            return node

    async def async_get_call_target(self, call_id: str) -> Optional[BaseNode]:
        """Get the target node of a call."""
        async with self._semaphore:
            return await self.repos.call_repo.get_target(call_id)

    async def async_ensure_targets_edges_batch(
        self,
        edges: List[Tuple[str, str]],
    ) -> None:
        """Batch async ensure targets edges."""
        if not edges:
            return
        try:
            query = """
            FOR edge IN @edges
                UPSERT { _from: edge.from_id, _to: edge.to_id }
                INSERT { _from: edge.from_id, _to: edge.to_id }
                UPDATE {}
                IN targets_edges
            """
            await self.repos.targets_edges.db.aql.execute(
                query,
                bind_vars={"edges": [{"from_id": f, "to_id": t}
                                     for f, t in edges]}
            )
        except Exception as e:
            print(f"Error ensuring targets edges batch: {e}")
            # logger.error(
            #     f"Error ensuring targets edges batch: {e}"
            # )

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
        return self.repos.nodes
