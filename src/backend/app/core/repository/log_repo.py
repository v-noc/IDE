from typing import Any, Optional, List, Dict, Tuple

from app.core.model import LogNode
from app.core.repository.base.base_collection import BaseRepository
from arangoasync.database import AsyncDatabase
# from arango.cursor import Cursor


class LogRepository(BaseRepository[LogNode]):

    def __init__(self, db: AsyncDatabase):
        super().__init__(db, "logs", LogNode)

    async def find_enter_log(
        self,
        function_id: str,
        chain_id: str,
    ) -> Optional[LogNode]:
        query = """
            FOR e IN @@log_to_function_edges
            FILTER e._to == @function_id
            FOR l IN @@logs
                FILTER l._id == e._from
                AND l.chain_id == @chain_id
                AND l.event_type == "enter"
                LIMIT 1
                RETURN l
        """
        bind_vars = {
            "@log_to_function_edges": "log_to_function_edges",
            "@logs": "logs",
            "function_id": function_id,
            "chain_id": chain_id,
        }
        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
        result = await cursor.next() if cursor else None
        return result or None

    async def find_parent_log(self, log_id: str) -> Optional[LogNode]:
        query = """
            FOR e IN @@log_to_log_edges
            FILTER e._from == @from_id
            FOR l IN @@logs
                FILTER l._id == e._to
                LIMIT 1
                RETURN l
        """
        bind_vars = {
            "@log_to_log_edges": "log_to_log_edges",
            "@logs": "logs",
            "from_id": log_id,
        }
        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
        result = await cursor.next() if cursor else None
        return result or None

    async def find_logs_for_function_chain(
        self, function_ids: List[str], start_function_id: str
    ) -> List[Dict[str, Any]]:
        bind_vars = {
            "function_ids": function_ids,
            "start_function_id": start_function_id,
            "@log_to_function_edges": "log_to_function_edges",
            "@log_to_log_edges": "log_to_log_edges",
        }

        query = """
            // Find chain ids for each function
            LET chains_per_function = (
                FOR func_id IN @function_ids
                    LET chains = (
                        FOR e IN @@log_to_function_edges
                            FILTER e._to == func_id
                            LET l = DOCUMENT(e._from)
                            RETURN DISTINCT l.chain_id
                    )
                    RETURN chains
            )

            // Intersection of chain ids across all functions
            LET candidate_chains = LENGTH(chains_per_function) > 0
                ? FIRST(chains_per_function)
                : []
            LET common_chains = (
                FOR chain_id IN candidate_chains
                    LET missing_in_any = (
                        FOR arr IN chains_per_function
                            FILTER chain_id NOT IN arr
                            LIMIT 1
                            RETURN true
                    )
                    FILTER LENGTH(missing_in_any) == 0
                    RETURN chain_id
            )

            // Pick ENTER log for the start function within the common chain
            LET start_log = FIRST(
                FOR chain_id IN common_chains
                    FOR e IN @@log_to_function_edges
                        FILTER e._to == @start_function_id
                        LET l = DOCUMENT(e._from)
                        FILTER l != null
                            && l.chain_id == chain_id
                            && l.event_type == 'enter'
                        SORT l.timestamp ASC
                        LIMIT 1
                        RETURN l
            )

            FILTER start_log != null

            // Traverse from the start to collect its subtree (children, ...)
            FOR v IN 0..100 INBOUND start_log._id @@log_to_log_edges
                LET parent_doc = FIRST(
                    FOR pe IN @@log_to_log_edges
                        FILTER pe._from == v._id
                        RETURN DOCUMENT(pe._to)
                )
                SORT v.timestamp
                RETURN {
                    "vertex": v,
                    "parent_id": parent_doc._id
                }
        """

        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
        results = []
        async for doc in cursor:
            results.append(doc)
        return results

    async def find_function_log(self, function_id: str) -> List[Dict[str, Any]]:
        query = """
            // Collect ENTER logs for the function as starting points
            LET start_logs = (
                FOR e IN @@log_to_function_edges
                    FILTER e._to == @function_id
                    LET l = DOCUMENT(e._from)
                    FILTER l != null && l.event_type == 'enter'
                    RETURN l
            )

            // For each start log, traverse INBOUND (child -> parent orientation)
            // to collect the containment subtree including the start node
            FOR start IN start_logs
                FOR v, e, p IN 0..@max_depth INBOUND start._id @@log_to_log_edges
                    OPTIONS { order: "bfs" }
                    RETURN {
                        "vertex": v,
                        "parent_id": LENGTH(p.vertices) >= 2
                            ? p.vertices[-2]._id
                            : null
                    }
         """
        bind_vars = {
            "@log_to_function_edges": "log_to_function_edges",
            "@log_to_log_edges": "log_to_log_edges",
            "function_id": function_id,
            "max_depth": 50,
        }
        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
        results = []
        async for doc in cursor:
            results.append(doc)
        return results

    async def get_containment_tree(
        self, start_log_id: str, depth: int | str = 50
    ) -> List[Dict[str, Any]]:
        max_depth = 50 if depth == "*" else depth
        query = """
        FOR v, e, p IN 1..@max_depth INBOUND @start_log_id @@log_edges
            OPTIONS { order: "bfs" }
            RETURN {
                "vertex": v,
                "parent_id": p.vertices[-2]._id
            }
        """
        bind_vars = {
            "start_log_id": start_log_id,
            "@log_edges": "log_to_log_edges",
            "max_depth": max_depth,
        }
        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
        results = []
        async for doc in cursor:
            results.append(doc)
        return results

    async def create_batch_edges(
        self,
        edges: List[Dict],  # [{"from_id": "...", "to_id": "..."}]
        edge_type: str,  # "log_to_function" or "log_to_log"
    ) -> Tuple[int, List[Dict]]:
        """
        Batch insert edges using efficient bulk operation.

        Args:
            edges: List of edge dictionaries with "from_id" and "to_id" keys
            edge_type: Type of edge collection ("log_to_function" or "log_to_log")

        Returns:
            Tuple of (count_created, errors) where errors is a list of error dicts
            with "index" and "message" keys

        Performance:
            - Sequential inserts: ~10ms per edge (1000 edges = 10 seconds)
            - Batch insert: ~200ms for 1000 edges (50x faster)
        """
        if not edges:
            return 0, []

        collection_name = f"{edge_type}_edges"

        # Ensure edge collection exists and is properly configured

        collection = self.db.collection(collection_name)

        # Build edge documents for batch insert
        edge_docs = [
            {
                "_from": edge["from_id"],
                "_to": edge["to_id"],
            }
            for edge in edges
        ]

        # Attempt batch insert first (fast path)
        try:
            results = await collection.insert_many(
                edge_docs,
                return_new=True,
                overwrite=False,  # Fail if edge already exists
            )
            # All succeeded
            return len(results), []
        except Exception:
            # Batch insert failed (likely due to duplicates or validation errors)
            # Fall back to individual inserts for detailed error reporting
            created_count = 0
            errors = []

            for idx, edge_doc in enumerate(edge_docs):
                try:
                    await collection.insert(edge_doc)
                    created_count += 1
                except Exception as individual_error:
                    errors.append({
                        "index": idx,
                        "message": str(individual_error),
                    })

            return created_count, errors

    async def create_batch(
        self,
        logs: List[LogNode],
    ) -> Tuple[List[LogNode], List[Dict[str, any]]]:
        """
        Batch insert logs.
        Returns: (created_logs, errors)
        errors = [{"index": 0, "message": "..."}]
        """
        # Convert models to dicts

        docs = [log.model_dump(by_alias=True, mode='json') for log in logs]

        # Use insert_many which is much faster than loops

        collection = self.db.collection("logs")
        result = await collection.insert_many(docs, return_new=True)

        # Wrap results back into Pydantic models
        return [LogNode(**res["new"]) for res in result]

    async def find_latest_enter_logs_batch(
        self,
        chain_function_pairs: List[Dict[str, str]]
    ) -> Dict[Tuple[str, str], str]:
        """
        Input: [{'chain_id': 'c1', 'function_id': 'f1'}, ...]
        Output: {('c1', 'f1'): 'logs/12345', ...}
        """
        if not chain_function_pairs:
            return {}

        query = """
            FOR pair IN @pairs
                // Find the latest 'enter' log for this specific chain+function
                LET latest_log = (
                    FOR l IN @@logs
                        FILTER l.chain_id == pair.chain_id
                        FILTER l.event_type == "enter"
                        // Check function via edge (expensive) or if you store function_id on log (faster).
                        // Assuming we rely on edges as per your schema:
                        FOR e IN @@log_to_function_edges
                            FILTER e._from == l._id
                            FILTER e._to == pair.function_id
                            SORT l.timestamp DESC
                            LIMIT 1
                            RETURN l
                )
                FILTER LENGTH(latest_log) > 0
                RETURN {
                    chain_id: pair.chain_id,
                    function_id: pair.function_id,
                    log_id: latest_log[0]._id
                }
        """

        bind_vars = {
            "@logs": "logs",
            "@@logs": "logs",  # standard collection bind
            "@log_to_function_edges": "log_to_function_edges",
            "pairs": chain_function_pairs
        }

        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)

        # Convert to easy lookup map: (chain_id, function_id) -> log_id
        results = {}
        async for doc in cursor:
            results[(doc["chain_id"], doc["function_id"])] = doc["log_id"]
        return results
