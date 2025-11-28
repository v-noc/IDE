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

    def create_call_site(self, caller_id: str, callee_id: str, call_site: CallSiteModel) -> None:
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

    def clear_db(self) -> None:
        """Clear all nodes and relationships."""
        self.conn.execute("MATCH (n) DETACH DELETE n")
