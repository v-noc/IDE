from typing import Any, Optional, List, Dict

from app.core.model import LogNode
from app.core.repository.base.base_collection import BaseRepository
from arango.database import StandardDatabase
# from arango.cursor import Cursor


class LogRepository(BaseRepository[LogNode]):

    def __init__(self, db: StandardDatabase):
        super().__init__(db, "logs", LogNode)

    def find_enter_log(
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
        results = self.aql(query, bind_vars=bind_vars)
        return results[0] if results else None

    def find_parent_log(self, log_id: str) -> Optional[LogNode]:
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
        results = self.aql(query, bind_vars=bind_vars)
        return results[0] if results else None

    def find_logs_for_function_chain(
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

        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        return list(cursor)

    def find_function_log(self, function_id: str) -> List[Dict[str, Any]]:
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
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        return list(cursor)

    def get_containment_tree(
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
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        return list(cursor)
