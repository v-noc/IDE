from typing import Any, Optional, List, Dict

from app.core.model import LogNode
from app.core.repository.base.base_collection import BaseRepository
from arango.database import StandardDatabase


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
            FILTER l._id == e._from AND l.chain_id == @chain_id AND l.event_type == "enter"
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

    def find_function_log(self, function_id: str) -> List[Dict[str, Any]]:
        query = """
        LET function_log_ids = (
            FOR e IN @@log_to_function_edges
                FILTER e._to == @function_id
                RETURN e._from
        )

        FOR log_id IN function_log_ids
            LET log_doc = DOCUMENT(log_id)
            LET parent_doc = FIRST(
                FOR e IN @@log_to_log_edges
                    FILTER e._from == log_id
                    RETURN DOCUMENT(e._to)
            )
            RETURN { "vertex": log_doc, "parent_id": parent_doc._id }
        """
        bind_vars = {
            "@log_to_function_edges": "log_to_function_edges",
            "@log_to_log_edges": "log_to_log_edges",
            "function_id": function_id,
        }
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        return list(cursor)

    def get_containment_tree(self, start_log_id: str, depth: int | str = 50) -> List[Dict[str, Any]]:
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
