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
        print("find_parent_log", log_id)
        query = """
        FOR e IN log_to_log_edges
          FILTER e._from == @from_id
          FOR l IN logs
            FILTER l._id == e._to
            LIMIT 1
            RETURN l
        """
        bind_vars = {
            "from_id": log_id,
        }
        results = self.aql(query, bind_vars=bind_vars)
        return results[0] if results else None
