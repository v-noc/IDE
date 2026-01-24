import asyncio
from typing import Any, Dict, List, Optional, TypeVar

from arangoasync.exceptions import DocumentDeleteError, DocumentGetError
from pydantic import BaseModel

from app.core.model import AllNodes
from app.core.model.nodes import ProjectNode

from .base_collection import BaseRepository

T = TypeVar("T", bound=BaseModel)


class BaseNodeRepository(BaseRepository[T]):
    """Repository for node collections."""

    async def _delete_edges_for_node(self, ec_name: str, node_id: str) -> int:
        """
        Atomically delete all edges connected to node_id in a single edge collection.
        Uses the "collect keys first → remove" pattern to ensure consistency.
        Returns the number of edges removed.
        """
        query = """
            LET connected_keys = (
                FOR e IN @@ec
                    FILTER e._from == @node_id OR e._to == @node_id
                    RETURN e._key
            )
            FOR key IN connected_keys
                REMOVE key IN @@ec
            RETURN LENGTH(connected_keys)
        """
        bind_vars = {
            "@ec": ec_name,
            "node_id": node_id
        }
        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
        async for result in cursor:
            return result  # the length
        return 0

    async def cascade_delete(
        self,
        start_node_id: str,
        max_depth: int = 50,
    ) -> Dict[str, Any]:
        """
        Cascade delete a node and all its descendants in a single AQL query.

        This method:
        - Collects all descendant vertex IDs via graph traversal (deduplicated)
        - Deletes edges from all fixed edge collections (contains_edges,
          targets_edges, log_to_function_edges, log_to_log_edges)
        - Deletes all vertices
        - Returns counts of what was deleted

        Args:
            start_node_id: The _id of the starting node (e.g., "nodes/123")
            max_depth: Maximum traversal depth (default: 50)

        Returns:
            Dict with keys:
                - removed_vertices: Number of vertices deleted
                - removed_contains_edges: Number of contains_edges deleted
                - removed_targets_edges: Number of targets_edges deleted
                - removed_log_to_function_edges: Number deleted
                - removed_log_to_log_edges: Number deleted
                - removed_documents: Number of documents deleted
                - total_vertex_ids_collected: Total vertex IDs collected
        """
        query = """
            LET startId = @start_node_id
            LET maxDepth = @max_depth

            // 1) Get Start Node Data explicitly first
            LET startNode = DOCUMENT(startId)
            
            // If start doesn't exist, stop here
            FILTER startNode != null

            // 2) Traverse: Collect _id AND documents list immediately
            LET descendantsData = (
                FOR v IN 1..maxDepth OUTBOUND startId contains_edges
                OPTIONS { uniqueVertices: "global", order: "bfs" }
                FILTER v != null
                RETURN { id: v._id, docs: v.documents }
            )

            // 3) Combine Start Node data + Descendant data
            // We now have a list of objects: [{ id: "nodes/1", docs: [...] }, ...]
            LET allNodeData = APPEND(
                [{ id: startNode._id, docs: startNode.documents }], 
                descendantsData
            )

            // Extract just the IDs list for edge operations (Deduplicated)
            LET allIds = UNIQUE(allNodeData[*].id)

            // --- EDGE DELETIONS (Uses allIds) ---

            LET removedContains = (
                FOR e IN contains_edges
                    FILTER e._from IN allIds OR e._to IN allIds
                    REMOVE e IN contains_edges OPTIONS { ignoreErrors: true }
                    RETURN 1
            )

            LET removedTargets = (
                FOR e IN targets_edges
                    FILTER e._from IN allIds OR e._to IN allIds
                    REMOVE e IN targets_edges OPTIONS { ignoreErrors: true }
                    RETURN 1
            )

            LET removedLogToFunction = (
                FOR e IN log_to_function_edges
                    FILTER e._from IN allIds OR e._to IN allIds
                    REMOVE e IN log_to_function_edges OPTIONS { ignoreErrors: true }
                    RETURN 1
            )

            LET removedLogToLog = (
                FOR e IN log_to_log_edges
                    FILTER e._from IN allIds OR e._to IN allIds
                    REMOVE e IN log_to_log_edges OPTIONS { ignoreErrors: true }
                    RETURN 1
            )

            // --- DOCUMENT DELETION (Uses allNodeData) ---
            
            // 4) Extract Document Keys directly from the data we already fetched.
            // No need to call DOCUMENT() again.
            LET docKeysToDelete = UNIQUE(
                FOR item IN allNodeData
                    FILTER IS_ARRAY(item.docs) // Ensure the node actually had a list
                    FOR docId IN item.docs
                        FILTER docId != null
                        // Parse to ensure we only delete things in 'documents' collection
                        LET parsed = PARSE_IDENTIFIER(docId)
                        FILTER parsed.collection == "documents"
                        RETURN parsed.key
            )

            LET removedDocuments = (
                FOR key IN docKeysToDelete
                    REMOVE { _key: key } IN documents OPTIONS { ignoreErrors: true }
                    RETURN 1
            )

            // --- VERTEX DELETION ---

            LET removedVertices = (
                FOR vid IN allIds
                    // Ensure we only delete from 'nodes' collection to be safe
                    LET parsed = PARSE_IDENTIFIER(vid)
                    FILTER parsed.collection == "nodes"
                    REMOVE { _key: parsed.key } IN nodes OPTIONS { ignoreErrors: true }
                    RETURN 1
            )

            RETURN {
                docKeysToDelete: docKeysToDelete,
                removed_vertices: LENGTH(removedVertices),
                removed_contains_edges: LENGTH(removedContains),
                removed_targets_edges: LENGTH(removedTargets),
                removed_log_to_function_edges: LENGTH(removedLogToFunction),
                removed_log_to_log_edges: LENGTH(removedLogToLog),
                removed_documents: LENGTH(removedDocuments),
                total_vertex_ids_collected: LENGTH(allIds)
            }
        """

        try:
            cursor = await self.db.aql.execute(
                query,
                bind_vars={
                    "start_node_id": start_node_id,
                    "max_depth": max_depth,
                }
            )
            result = None

            async for row in cursor:
                result = row

                break

            # If start node doesn't exist, return empty counts
            if result is None:
                return {
                    "removed_vertices": 0,
                    "removed_contains_edges": 0,
                    "removed_targets_edges": 0,
                    "removed_log_to_function_edges": 0,
                    "removed_log_to_log_edges": 0,
                    "removed_documents": 0,
                    "total_vertex_ids_collected": 0,
                }

            return result
        except Exception as e:
            print(f"Cascade delete failed: {e}")
            return {
                "removed_vertices": 0,
                "removed_contains_edges": 0,
                "removed_targets_edges": 0,
                "removed_log_to_function_edges": 0,
                "removed_log_to_log_edges": 0,
                "removed_documents": 0,
                "total_vertex_ids_collected": 0,
            }

    async def delete(self, key: str) -> bool:
        node_id = f"{self.collection_name}/{key}"

        # 1. Get edge collections (cached)
        edge_collections = await self._get_edge_collections()

        # 2. Delete edges concurrently, but collect results
        delete_tasks = [
            self._delete_edges_for_node(ec_name, node_id)
            for ec_name in edge_collections
        ]

        results = await asyncio.gather(*delete_tasks, return_exceptions=True)

        # Check for failures
        failed = [r for r in results if isinstance(r, Exception)]
        if failed:
            # logger.error(f"Failed to delete edges for {node_id}: {failed}")
            return False  # Do NOT delete the node if any edge cleanup failed

        # Optional: total_removed = sum(r for r in results if isinstance(r, int))

        # 3. Delete the node itself
        try:
            collection = await self.get_collection()
            await collection.delete(key)
            return True
        except (DocumentDeleteError, DocumentGetError):
            return False

    async def create_batch(self, nodes: List[T]) -> List[T]:
        """Batch create multiple nodes."""
        if not nodes:
            return []

        # Serialize all
        dumps = [
            node.model_dump(by_alias=True, exclude_none=True, mode="json")
            for node in nodes
        ]

        # Batch insert
        collection = await self.get_collection()
        results = await collection.insert_many(
            dumps,
            return_new=True,
            overwrite=False
        )

        return [self._validate(r["new"]) for r in results]

    async def update_batch(self, nodes: List[T]) -> List[T]:
        """Batch update multiple nodes."""
        if not nodes:
            return []

        dumps = [
            node.model_dump(by_alias=True, exclude_none=True, mode="json")
            for node in nodes
        ]

        collection = await self.get_collection()
        # update_many expects dicts with _key or _id
        results = await collection.update_many(
            dumps,
            return_new=True,
            merge_objects=True
        )
        return [self._validate(r["new"]) for r in results]

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
        result = None

        async for row in cursor:
            result = row
            break  # Get first and exit

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
        result = None
        async for row in cursor:
            result = row
            break  # Get first and exit

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
                PRUNE v == null || v.status != "active" 
                OPTIONS { order: "bfs", uniqueVertices: "global" }


                LET parent_candidates = (
                    FOR i IN 2..LENGTH(p.vertices)
                        LET candidate = p.vertices[LENGTH(p.vertices) - i]
                        FILTER candidate.node_type NOT IN @exclude_types
                        LIMIT 1
                        RETURN candidate._id
                )

                // 5. EXCLUDE TYPES FROM OUTPUT
                FILTER v != null
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
        try:
            # Note: This returns raw dicts, not Pydantic models directly,
            # because the structure is custom ("vertex", "parent_id").
            cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
            # Buffer all results (for backwards compatibility)
            results = []
            async for doc in cursor:
                results.append(doc)
            return results
        except Exception as e:
            print(f"Error getting containment tree: {e}")
            return []

    async def get_nearest_file_and_project(self, node_id: str) -> Dict[str, Any]:
        """Return nearest file and project ancestors in one traversal.

        Performs a BFS INBOUND traversal on contains_edges starting from
        node_id. Selects first encountered file and project nodes.

        Returns a dict with keys file and project whose values are the raw
        vertex documents or None if not found.
        """
        try:
            query = """
            LET file = FIRST(
                FOR v IN 1..50 INBOUND @start_node_id @@contains_collection
                    OPTIONS { order: "bfs" }
                    FILTER v.node_type == "file"
                    LIMIT 1
                    RETURN v
            )

            LET project = FIRST(
                FOR v IN 1..50 INBOUND @start_node_id @@contains_collection
                    OPTIONS { order: "bfs" }
                    FILTER v.node_type == "project"
                    LIMIT 1
                    RETURN v
            )

            RETURN { file, project }
            """
            bind_vars = {
                "start_node_id": node_id,
                "@contains_collection": "contains_edges",
            }
            cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
            result = None
            async for row in cursor:
                result = row
                break  # Get first and exit

            return result or {"file": None, "project": None}
        except Exception as e:
            print(f"Error getting nearest file and project: {e}")
            return {"file": None, "project": None}

    async def find_by_qname(self, qname: str) -> Optional[T]:
        return await self.find_one({"qname": qname})

    async def get_by_ids(self, ids: List[str]) -> Dict[str, T]:
        """Fetch multiple nodes by their keys."""
        if not ids:
            return {}

        clean_ids = [i.split("/")[-1] if "/" in i else i for i in ids]

        query = """
            FOR n IN @@collection
                FILTER n._key IN @ids
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

    async def get_by_qnames(self, qnames: List[str]) -> Dict[str, T]:
        """Fetch multiple nodes by their qualified names."""
        if not qnames:
            return {}

        query = """
            FOR n IN @@collection
                FILTER n.qname IN @qnames
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

    async def find_by_type(self, node_type: str) -> List[T]:
        return await self.find({"node_type": node_type})

    async def get_children(self, node_id: str) -> List[T]:
        """Async get a node's children."""

        query = """
        FOR v, e, p IN 1..1 OUTBOUND @start_node_id @@contains_collection
            OPTIONS { order: "bfs" }
            RETURN v
        """
        bind_vars = {
            "start_node_id": node_id,
            "@contains_collection": "contains_edges"
        }
        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
        results = []
        async for doc in cursor:
            results.append(doc)
        return results

    async def move_node(self, node_id: str, new_parent_id: str) -> None:
        """
        Move a node to a new parent.
        1. Remove all incoming 'contains_edges' to this node (detach from old parent).
        2. Create new edge from new_parent_id to node_id.
        """
        # 1. Remove old edges
        remove_query = """
        FOR e IN @@contains_collection
            FILTER e._to == @node_id
            REMOVE e IN @@contains_collection
        """
        await self.db.aql.execute(
            remove_query,
            bind_vars={
                "node_id": node_id,
                "@contains_collection": "contains_edges"
            }
        )

        # 2. Insert new edge
        insert_query = """
        INSERT { 
            _from: @parent_id, 
            _to: @node_id
        } INTO @@contains_collection
        """
        await self.db.aql.execute(
            insert_query,
            bind_vars={
                "parent_id": new_parent_id,
                "node_id": node_id,
                "@contains_collection": "contains_edges"
            }
        )

    async def move_batch(self, moves: List[tuple[str, str]]) -> None:
        """
        Batch move nodes.
        moves: List of (child_id, new_parent_id)

        NOTE: This operation modifies 'contains_edges' which is also queried.
        In AQL, you cannot modify a collection while iterating over it in the
        same query if the modification affects the iteration.
        """
        if not moves:
            return

        child_ids = []
        for m in moves:
            cid = m[0]
            if "/" not in cid:
                cid = f"nodes/{cid}"
            child_ids.append(cid)

        remove_query = """
        FOR e IN @@contains_collection
            FILTER e._to IN @child_ids
            REMOVE e IN @@contains_collection
        """
        await self.db.aql.execute(
            remove_query,
            bind_vars={
                "child_ids": child_ids,
                "@contains_collection": "contains_edges"
            }
        )

        # 2. Insert new edges

        insert_query = """
            FOR m IN @moves
                INSERT {
                    _from: CONTAINS(m.parent_id, "/") ? m.parent_id : CONCAT(
                        "nodes/", m.parent_id),
                    _to: CONTAINS(m.child_id, "/") ? m.child_id : CONCAT(
                        "nodes/", m.child_id)
                } INTO @@contains_collection
        """
        await self.db.aql.execute(
            insert_query,
            bind_vars={
                "moves": [
                    {
                        "child_id": c if "/" in c else f"nodes/{c}",
                        "parent_id": p if "/" in p else f"nodes/{p}",
                    }
                    for c, p in moves
                ],
                "@contains_collection": "contains_edges"
            }
        )

    async def delete_batch(self, keys: List[str]) -> List[bool]:
        """
        Batch delete multiple nodes and all their connected edges asynchronously.

        Executes deletions in parallel (concurrent per node, with concurrent edge deletion inside each).

        Returns:
            List[bool]: Success status for each key in the input order (True if node was deleted).

        Performance:
            - Scales well with number of nodes (full parallelism).
            - Each node follows the same optimized strategy as single delete (~70ms per node).
        """
        if not keys:
            return []

        # Run all individual deletes concurrently
        tasks = [self.delete(key) for key in keys]
        results = await asyncio.gather(*tasks)

        return results
