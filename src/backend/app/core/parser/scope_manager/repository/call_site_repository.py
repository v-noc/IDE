import gc
from typing import List, Optional

from ..db import DBConnectionManager
from ..models import CallSiteModel


class CallSiteRepository:
    """Repository for call site operations."""

    def __init__(self, db_manager: DBConnectionManager):
        self.db_manager = db_manager

    async def create_call_site(
        self,
        caller_id: str,
        callee_id: Optional[str],
        call_site: CallSiteModel,
        prev_call_site_id: Optional[str] = None,
    ) -> None:
        """Create a call site node and link it to caller/callee."""
        # Create CallSite node
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                CREATE (cs:CallSite {
                    id: $id,
                    line: $line,
                    col: $col,
                    name: $name
                })
                """,
                {
                    "id": call_site.id,
                    "line": call_site.line,
                    "col": call_site.col,
                    "name": call_site.name,
                },
            )
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

        # Link to Caller
        result = None
        try:
            result = await conn.execute(
                """
                MATCH (caller:Scope {id: $caller_id}),
                      (cs:CallSite {id: $cs_id})
                CREATE (caller)-[:HAS_CALL_SITE]->(cs)
                """,
                {"caller_id": caller_id, "cs_id": call_site.id},
            )
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

        # Link to Callee (if resolved)
        if callee_id:
            result = None
            try:
                result = await conn.execute(
                    """
                    MATCH (cs:CallSite {id: $cs_id})
                    MATCH (callee:Scope {id: $callee_id})
                    CREATE (cs)-[:TARGETS]->(callee)
                    """,
                    {"cs_id": call_site.id, "callee_id": callee_id},
                )
            finally:
                if result is not None:
                    del result
                    gc.collect()  # Force immediate cleanup of the C++ object

        # Link to previous call site (if chained)
        if prev_call_site_id:
            result = None
            try:
                result = await conn.execute(
                    """
                    MATCH (prev:CallSite {id: $prev_id})
                    MATCH (curr:CallSite {id: $curr_id})
                    CREATE (prev)-[:NEXT_IN_CHAIN]->(curr)
                    """,
                    {"prev_id": prev_call_site_id, "curr_id": call_site.id},
                )
            finally:
                if result is not None:
                    del result
                    gc.collect()  # Force immediate cleanup of the C++ object

    async def batch_create_call_sites(
        self,
        call_sites: List[dict],
    ) -> None:
        """
        Batch create multiple call sites efficiently using Neo4j UNWIND.

        Args:
            call_sites: List of dicts with keys:
                - call_site: CallSiteModel
                - caller_id: str
                - callee_id: Optional[str]
                - prev_call_site_id: Optional[str]
        """
        if not call_sites:
            return

        # Prepare data for UNWIND
        call_site_data = []
        for item in call_sites:
            call_site = item["call_site"]
            call_site_data.append({
                "id": call_site.id,
                "line": call_site.line,
                "col": call_site.col,
                "name": call_site.name,
                "caller_id": item["caller_id"],
                "callee_id": item.get("callee_id"),
                "prev_call_site_id": item.get("prev_call_site_id"),
            })

        # Batch create all CallSite nodes
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                UNWIND $call_sites AS cs_data
                CREATE (cs:CallSite {
                    id: cs_data.id,
                    line: cs_data.line,
                    col: cs_data.col,
                    name: cs_data.name
                })
                """,
                {"call_sites": call_site_data},
            )
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

        # Batch create HAS_CALL_SITE relationships
        result = None
        try:
            result = await conn.execute(
                """
                UNWIND $call_sites AS cs_data
                MATCH (caller:Scope {id: cs_data.caller_id})
                MATCH (cs:CallSite {id: cs_data.id})
                CREATE (caller)-[:HAS_CALL_SITE]->(cs)
                """,
                {"call_sites": call_site_data},
            )
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

        # Batch create TARGETS relationships (only for those with callee_id)
        targets_data = [
            {"cs_id": cs["id"], "callee_id": cs["callee_id"]}
            for cs in call_site_data
            if cs["callee_id"]
        ]
        if targets_data:
            result = None
            try:
                result = await conn.execute(
                    """
                    UNWIND $targets AS t
                    MATCH (cs:CallSite {id: t.cs_id})
                    MATCH (callee:Scope {id: t.callee_id})
                    CREATE (cs)-[:TARGETS]->(callee)
                    """,
                    {"targets": targets_data},
                )
            finally:
                if result is not None:
                    del result
                    gc.collect()  # Force immediate cleanup of the C++ object

        # Batch create NEXT_IN_CHAIN relationships (only for those with prev_call_site_id)
        chain_data = [
            {"prev_id": cs["prev_call_site_id"], "curr_id": cs["id"]}
            for cs in call_site_data
            if cs["prev_call_site_id"]
        ]
        if chain_data:
            result = None
            try:
                result = await conn.execute(
                    """
                    UNWIND $chains AS c
                    MATCH (prev:CallSite {id: c.prev_id})
                    MATCH (curr:CallSite {id: c.curr_id})
                    CREATE (prev)-[:NEXT_IN_CHAIN]->(curr)
                    """,
                    {"chains": chain_data},
                )
            finally:
                if result is not None:
                    del result
                    gc.collect()  # Force immediate cleanup of the C++ object

    async def clear_calls_from_scope(self, scope_id: str) -> None:
        """Delete all call sites originating from the given scope."""
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                MATCH (s:Scope {id: $id})-[:HAS_CALL_SITE]->(root:CallSite)
                WHERE NOT EXISTS {
                    MATCH (:CallSite)-[:NEXT_IN_CHAIN]->(root)
                }
                MATCH path = (root)-[:NEXT_IN_CHAIN*0..]->(cs:CallSite)
                WITH DISTINCT cs
                DETACH DELETE cs
                """,
                {"id": scope_id},
            )
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def get_call_chain(self, call_site_id: str) -> List[CallSiteModel]:
        """Get the full call chain starting from a call site."""
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                MATCH path = (
                    start:CallSite {id: $id}
                )-[:NEXT_IN_CHAIN*0..]->(cs:CallSite)
                RETURN cs
                ORDER BY length(path)
                """,
                {"id": call_site_id},
            )

            chain = []
            for row in result:
                node = row[0]
                chain.append(
                    CallSiteModel(
                        id=node["id"],
                        line=node["line"],
                        col=node["col"],
                        name=node.get("name"),
                    )
                )
            return chain
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def get_call_chain_roots(
        self,
        target_scope_id: Optional[str] = None,
    ) -> List[CallSiteModel]:
        """
        Get call sites that start a chain (no incoming NEXT_IN_CHAIN).

        If `target_scope_id` is provided, only include roots whose chain
        targets that scope.
        """
        conn = self.db_manager.get_connection()
        result = None
        try:
            if target_scope_id is None:
                result = await conn.execute(
                    """
                    MATCH (cs:CallSite)
                    WHERE NOT EXISTS {
                        MATCH (:CallSite)-[:NEXT_IN_CHAIN]->(cs)
                    }
                    RETURN cs
                    """
                )
            else:
                result = await conn.execute(
                    """
                    MATCH (root:CallSite)
                    WHERE NOT EXISTS {
                        MATCH (:CallSite)-[:NEXT_IN_CHAIN]->(root)
                    }
                    MATCH path = (root)-[:NEXT_IN_CHAIN*0..]->(cs:CallSite)
                    MATCH (cs)-[:TARGETS]->(
                        scope:Scope {id: $target_scope_id}
                    )
                    RETURN DISTINCT root AS cs
                    """,
                    {"target_scope_id": target_scope_id},
                )

            roots = []
            for row in result:
                node = row[0]
                roots.append(
                    CallSiteModel(
                        id=node["id"],
                        line=node["line"],
                        col=node["col"],
                        name=node.get("name"),
                    )
                )
            return roots
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object
