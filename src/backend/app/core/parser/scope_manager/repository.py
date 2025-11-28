from .db import DBConnectionManager
from .models import ScopeModel, CallSiteModel
from typing import List, Optional
import uuid


class ScopeRepository:
    def __init__(self, db_manager: DBConnectionManager):
        self.conn = db_manager.get_connection()

    def create_scope(self, scope: ScopeModel) -> None:
        """Create a Scope node."""
        self.conn.execute(
            """
            CREATE (s:Scope {
                id: $id,
                name: $name,
                qname: $qname,
                type: $type,
                file_path: $file_path,
                start_line: $start_line,
                start_col: $start_col,
                end_line: $end_line,
                end_col: $end_col,
                base_classes: $base_classes,
                mro: $mro
            })
            """,
            {
                "id": scope.id,
                "name": scope.name,
                "qname": scope.qname,
                "type": scope.type.value,
                "file_path": scope.file_path,
                "start_line": scope.start_line,
                "start_col": scope.start_col,
                "end_line": scope.end_line,
                "end_col": scope.end_col,
                "base_classes": scope.base_classes,
                "mro": scope.mro,
            }
        )

    def get_scope_by_id(self, scope_id: str) -> Optional[ScopeModel]:
        """Get a Scope by ID."""
        result = self.conn.execute(
            "MATCH (s:Scope {id: $id}) RETURN s",
            {"id": scope_id}
        )

        for row in result:
            node = row[0]
            return ScopeModel(
                id=node["id"],
                name=node["name"],
                qname=node["qname"],
                type=node["type"],
                file_path=node["file_path"],
                start_line=node["start_line"],
                start_col=node["start_col"],
                end_line=node["end_line"],
                end_col=node["end_col"],
                base_classes=node.get("base_classes", []),
                mro=node.get("mro", []),
            )
        return None

    def get_scope_by_qname(self, qname: str) -> Optional[ScopeModel]:
        """Get a Scope by qualified name."""
        result = self.conn.execute(
            "MATCH (s:Scope {qname: $qname}) RETURN s",
            {"qname": qname}
        )

        for row in result:
            node = row[0]
            return ScopeModel(
                id=node["id"],
                name=node["name"],
                qname=node["qname"],
                type=node["type"],
                file_path=node["file_path"],
                start_line=node["start_line"],
                start_col=node["start_col"],
                end_line=node["end_line"],
                end_col=node["end_col"],
                base_classes=node.get("base_classes", []),
                mro=node.get("mro", []),
            )
        return None

    def create_contains_edge(self, parent_id: str, child_id: str) -> None:
        """Create CONTAINS relationship from parent to child."""
        self.conn.execute(
            """
            MATCH (p:Scope {id: $parent_id}), (c:Scope {id: $child_id})
            CREATE (p)-[:CONTAINS]->(c)
            """,
            {"parent_id": parent_id, "child_id": child_id}
        )

    def create_call_site(self, caller_id: str, callee_id: str, call_site: CallSiteModel, prev_call_site_id: Optional[str] = None) -> None:
        """Create CallSite and relationships."""
        # Create the CallSite node
        self.conn.execute(
            """
            CREATE (cs:CallSite {
                id: $id,
                line: $line,
                col: $col
            })
            """,
            {
                "id": call_site.id,
                "line": call_site.line,
                "col": call_site.col,
            }
        )

        # Create HAS_CALL_SITE edge from caller
        self.conn.execute(
            """
            MATCH (caller:Scope {id: $caller_id}), (cs:CallSite {id: $cs_id})
            CREATE (caller)-[:HAS_CALL_SITE]->(cs)
            """,
            {"caller_id": caller_id, "cs_id": call_site.id}
        )

        # Create TARGETS edge to callee
        self.conn.execute(
            """
            MATCH (cs:CallSite {id: $cs_id}), (callee:Scope {id: $callee_id})
            CREATE (cs)-[:TARGETS]->(callee)
            """,
            {"cs_id": call_site.id, "callee_id": callee_id}
        )

        # Create NEXT_IN_CHAIN edge if prev_call_site_id is provided
        if prev_call_site_id:
            self.conn.execute(
                """
                MATCH (prev:CallSite {id: $prev_id}), (curr:CallSite {id: $curr_id})
                CREATE (prev)-[:NEXT_IN_CHAIN]->(curr)
                """,
                {"prev_id": prev_call_site_id, "curr_id": call_site.id}
            )

    def get_all_scopes(self) -> List[ScopeModel]:
        """Get all scopes."""
        result = self.conn.execute("MATCH (s:Scope) RETURN s")
        scopes = []
        for row in result:
            node = row[0]
            scopes.append(ScopeModel(
                id=node["id"],
                name=node["name"],
                qname=node["qname"],
                type=node["type"],
                file_path=node["file_path"],
                start_line=node["start_line"],
                start_col=node["start_col"],
                end_line=node["end_line"],
                end_col=node["end_col"],
                base_classes=node.get("base_classes", []),
                mro=node.get("mro", []),
            ))
        return scopes

    def get_call_chain(self, call_site_id: str) -> List[CallSiteModel]:
        """Get the full call chain starting from a call site."""
        result = self.conn.execute(
            """
            MATCH path = (start:CallSite {id: $id})-[:NEXT_IN_CHAIN*0..]->(cs:CallSite)
            RETURN cs
            ORDER BY length(path)
            """,
            {"id": call_site_id}
        )

        chain = []
        for row in result:
            node = row[0]
            chain.append(CallSiteModel(
                id=node["id"],
                line=node["line"],
                col=node["col"],
            ))
        return chain

    def get_call_chain_roots(self, target_scope_id: Optional[str] = None) -> List[CallSiteModel]:
        """
        Get all call sites that start a chain (no incoming NEXT_IN_CHAIN edge).

        If `target_scope_id` is provided, only return those root call sites for which
        there exists a path along `NEXT_IN_CHAIN` that contains a call site targeting
        the given scope.
        """
        if target_scope_id is None:
            result = self.conn.execute(
                """
                MATCH (cs:CallSite)
                WHERE NOT EXISTS { MATCH (:CallSite)-[:NEXT_IN_CHAIN]->(cs) }
                RETURN cs
                """
            )
        else:
            result = self.conn.execute(
                """
                MATCH (root:CallSite)
                WHERE NOT EXISTS { MATCH (:CallSite)-[:NEXT_IN_CHAIN]->(root) }
                MATCH path = (root)-[:NEXT_IN_CHAIN*0..]->(cs:CallSite)
                MATCH (cs)-[:TARGETS]->(scope:Scope {id: $target_scope_id})
                RETURN DISTINCT root AS cs
                """,
                {"target_scope_id": target_scope_id},
            )

        roots = []
        for row in result:
            node = row[0]
            roots.append(CallSiteModel(
                id=node["id"],
                line=node["line"],
                col=node["col"],
            ))
        return roots

    def clear_db(self) -> None:
        """Clear all nodes and relationships."""
        self.conn.execute("MATCH (n) DETACH DELETE n")
