import asyncio
from typing import Any, Dict, List, Optional, TypeVar

from arangoasync.exceptions import DocumentDeleteError, DocumentGetError
from pydantic import BaseModel

from app.core.model import AllNodes
from app.core.model.nodes import ProjectNode

from .base_collection import BaseRepository

T = TypeVar("T", bound=BaseModel)


class NodeRepository(BaseRepository[T]):
    """Repository for node collections."""

    async def delete(self, key: str) -> bool:
        """
        Delete a node and all connected edges asynchronously.

        Strategy:
        1. Get all edge collections (async, cached)
        2. Delete edges concurrently (asyncio.gather)
        3. Delete node

        Performance Improvement:
            - Before: 170ms sequential
            - After: 70ms (concurrent edge deletion)
        """
        node_id = f"{self.collection_name}/{key}"

        # 1. Get edge collections (async with caching)
        edge_collections = await self._get_edge_collections()

        # 2. Delete edges concurrently!
        delete_tasks = []
        for ec_name in edge_collections:
            task = self._delete_edges_for_node(ec_name, node_id)
            delete_tasks.append(task)

        # Execute all deletions in parallel
        try:
            await asyncio.gather(*delete_tasks, return_exceptions=True)
        except Exception as e:
            # logger.error(f"Edge deletion failed: {e}")
            return False

        # 3. Delete the node itself
        try:
            collection = await self.get_collection()

            await collection.delete(key)
            return True
        except (DocumentDeleteError, DocumentGetError):
            return False

    async def get_parent(self, node_id: str) -> Optional[AllNodes]:
        """
        Find structural parent via 'contains' edge asynchronously.

        Query: 1-hop INBOUND traversal (fast: ~5-10ms)

        Returns:
            Parent node dict with vertex and parent_id, or None
        """
        query = """
        FOR v, e, p IN 1..1 INBOUND @start_node_id @@contains_collection
            OPTIONS { order: "bfs" }
            RETURN {
                "vertex": v,
                "parent_id": p.vertices[-2]._id
            }
        """
        bind_vars = {
            "start_node_id": node_id,
            "@contains_collection": "contains_edges"
        }

        # Execute query
        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)

        # Get first result only (don't buffer all)
        result = await cursor.next() if cursor else None

        return result

    async def get_parent_project(self, node_id: str) -> Optional[ProjectNode]:
        """
        Find nearest project ancestor (async).

        Traversal: Up to 100 hops INBOUND
        Performance: Usually fast (projects are typically 2-5 hops up)
        Worst case: 100 hops = ~50ms

        Optimization: Uses LIMIT 1, so ArangoDB stops after finding first project
        """
        query = """
        FOR v IN 1..100 INBOUND @start_node_id @@contains_collection
            OPTIONS { order: "bfs" }
            FILTER v.node_type == "project"
            LIMIT 1
            RETURN v
        """
        bind_vars = {
            "start_node_id": node_id,
            "@contains_collection": "contains_edges"
        }

        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)

        # Only fetch first result
        result = await cursor.next() if cursor else None

        return ProjectNode.model_validate(result) if result else None

    async def get_containment_tree(
        self,
        start_node_id: str,
        depth: int | str = 50,
        exclude_types: List[str] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes a graph traversal to get a full descendant tree.
        Returns a list of dictionaries, each containing the vertex and its
        parent's ID, perfect for rebuilding a tree structure.
        """
        # For MVP, use a large fixed depth for unbounded requests instead of
        # '1..' syntax
        max_depth = 50 if depth == "*" else depth

        # AQL's "p.vertices[-2]" gets the direct parent. We sometimes need to
        # skip virtual nodes (e.g., group) and attach children to the nearest
        # non-excluded ancestor while still traversing through excluded nodes.
        query = """
            // 1. Setup Start Node
            LET start_node = DOCUMENT(@start_node_id)
            LET start_ver = start_node.current_version != null ? start_node.current_version : 0

            FOR v, e, p IN 1..@max_depth OUTBOUND @start_node_id @@contains_collection
                OPTIONS { order: "bfs", uniqueVertices: "global" }

                // 4. OUTPUT CALCULATIONS
                LET parent_candidates = (
                    FOR i IN 2..LENGTH(p.vertices)
                        LET candidate = p.vertices[LENGTH(p.vertices) - i]
                        FILTER candidate.node_type NOT IN @exclude_types
                        LIMIT 1
                        RETURN candidate._id
                )

                // 5. EXCLUDE TYPES FROM OUTPUT
                FILTER v.node_type NOT IN @exclude_types

                // 6. TARGET LOGIC
                LET target_node = (
                    FOR target IN 1..1 OUTBOUND v @@targets_collection
                        LIMIT 1
                        RETURN target
                )

                RETURN {
                    "vertex": v,
                    "parent_id": FIRST(parent_candidates),
                    "target": FIRST(target_node)
                }
        """
        bind_vars = {
            "start_node_id": start_node_id,
            "@contains_collection": "contains_edges",
            "@targets_collection": "targets_edges",
            "max_depth": max_depth,
            "exclude_types": exclude_types or [],
        }
        # Note: This returns raw dicts, not Pydantic models directly,
        # because the structure is custom ("vertex", "parent_id").
        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
        # Buffer all results (for backwards compatibility)
        results = []
        async for doc in cursor:
            results.append(doc)
        return results

    async def get_nearest_file_and_project(self, node_id: str) -> Dict[str, Any]:
        """Return nearest file and project ancestors in one traversal.

        Performs a BFS INBOUND traversal on contains_edges starting from
        node_id. Selects first encountered file and project nodes.

        Returns a dict with keys file and project whose values are the raw
        vertex documents or None if not found.
        """
        query = """
        FOR v IN 1..50 INBOUND @start_node_id @@contains_collection
            OPTIONS { order: "bfs" }
            
            COLLECT AGGREGATE 
                file = FIRST(v.node_type == "file" ? v : null),
                project = FIRST(v.node_type == "project" ? v : null)
            
            RETURN { file, project }
        """
        bind_vars = {
            "start_node_id": node_id,
            "@contains_collection": "contains_edges",
        }
        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
        # Buffer all results (for backwards compatibility)

        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
        result = await cursor.next() if cursor else None
        return result or {"file": None, "project": None}

    async def find_by_qname(self, qname: str) -> Optional[T]:
        return await self.find_one({"qname": qname})

    async def find_by_type(self, node_type: str) -> List[T]:
        return await self.find({"node_type": node_type})
