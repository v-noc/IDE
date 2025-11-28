from .db import DBConnectionManager
from .repository import ScopeRepository
from .models import ScopeModel, CallSiteModel, ScopeType
from typing import Optional, List
import uuid


class ScopeManager:
    """
    Facade/Service layer for managing scopes and call sites.
    Provides high-level operations for creating, querying, and managing code structure.
    """

    def __init__(self, project_name: str, db_path: Optional[str] = None):
        self.db_manager = DBConnectionManager(project_name, db_path)
        self.repository = ScopeRepository(self.db_manager)

    # Scope Management

    def create_scope(
        self,
        name: str,
        qname: str,
        scope_type: ScopeType,
        file_path: str,
        start_line: int,
        start_col: int,
        end_line: int,
        end_col: int,
        base_classes: List[str] = None,
        mro: List[str] = None,
        scope_id: Optional[str] = None,
    ) -> ScopeModel:
        """Create a new scope."""
        scope = ScopeModel(
            id=scope_id or str(uuid.uuid4()),
            name=name,
            qname=qname,
            type=scope_type,
            file_path=file_path,
            start_line=start_line,
            start_col=start_col,
            end_line=end_line,
            end_col=end_col,
            base_classes=base_classes or [],
            mro=mro or [],
        )
        self.repository.create_scope(scope)
        return scope

    def get_scope(self, scope_id: str) -> Optional[ScopeModel]:
        """Get a scope by ID."""
        return self.repository.get_scope_by_id(scope_id)

    def get_scope_by_qname(self, qname: str) -> Optional[ScopeModel]:
        """Get a scope by qualified name."""
        return self.repository.get_scope_by_qname(qname)

    def delete_scope(self, scope_id: str) -> None:
        """Delete a scope and its relationships."""
        # Note: In Kuzu, deleting a node with DETACH will remove all relationships
        self.repository.conn.execute(
            "MATCH (s:Scope {id: $id}) DETACH DELETE s",
            {"id": scope_id}
        )

    def get_all_scopes(self) -> List[ScopeModel]:
        """Get all scopes."""
        return self.repository.get_all_scopes()

    # Hierarchy Management

    def link_parent_child(self, parent_id: str, child_id: str) -> None:
        """Link a parent scope to a child scope (e.g., Class contains Function)."""
        self.repository.create_contains_edge(parent_id, child_id)

    def get_children(self, parent_id: str) -> List[ScopeModel]:
        """Get all children of a scope."""
        result = self.repository.conn.execute(
            """
            MATCH (p:Scope {id: $parent_id})-[:CONTAINS]->(c:Scope)
            RETURN c
            """,
            {"parent_id": parent_id}
        )

        children = []
        for row in result:
            node = row[0]
            children.append(ScopeModel(
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
        return children

    # Call Site Management

    def create_call(
        self,
        caller_id: str,
        callee_id: str,
        line: int,
        col: int,

    ) -> CallSiteModel:
        """Create a call site linking caller to callee."""
        call_site = CallSiteModel(
            id=str(uuid.uuid4()),
            line=line,
            col=col,
        )
        self.repository.create_call_site(caller_id, callee_id, call_site)
        return call_site

    def get_calls_from(self, caller_id: str) -> List[dict]:
        """Get all calls made from a scope."""
        result = self.repository.conn.execute(
            """
            MATCH (caller:Scope {id: $caller_id})-[:HAS_CALL_SITE]->(cs:CallSite)-[:TARGETS]->(callee:Scope)
            RETURN cs, callee
            """,
            {"caller_id": caller_id}
        )

        calls = []
        for row in result:
            cs_node = row[0]
            callee_node = row[1]
            calls.append({
                "call_site": CallSiteModel(
                    id=cs_node["id"],
                    line=cs_node["line"],
                    col=cs_node["col"],
                ),
                "callee": ScopeModel(
                    id=callee_node["id"],
                    name=callee_node["name"],
                    qname=callee_node["qname"],
                    type=callee_node["type"],
                    file_path=callee_node["file_path"],
                    start_line=callee_node["start_line"],
                    start_col=callee_node["start_col"],
                    end_line=callee_node["end_line"],
                    end_col=callee_node["end_col"],
                    base_classes=callee_node.get("base_classes", []),
                    mro=callee_node.get("mro", []),
                ),
            })
        return calls

    def get_calls_to(self, callee_id: str) -> List[dict]:
        """Get all calls made to a scope."""
        result = self.repository.conn.execute(
            """
            MATCH (caller:Scope)-[:HAS_CALL_SITE]->(cs:CallSite)-[:TARGETS]->(callee:Scope {id: $callee_id})
            RETURN cs, caller
            """,
            {"callee_id": callee_id}
        )

        calls = []
        for row in result:
            cs_node = row[0]
            caller_node = row[1]
            calls.append({
                "call_site": CallSiteModel(
                    id=cs_node["id"],
                    line=cs_node["line"],
                    col=cs_node["col"],
                ),
                "caller": ScopeModel(
                    id=caller_node["id"],
                    name=caller_node["name"],
                    qname=caller_node["qname"],
                    type=caller_node["type"],
                    file_path=caller_node["file_path"],
                    start_line=caller_node["start_line"],
                    start_col=caller_node["start_col"],
                    end_line=caller_node["end_line"],
                    end_col=caller_node["end_col"],
                    base_classes=caller_node.get("base_classes", []),
                    mro=caller_node.get("mro", []),
                ),
            })
        return calls

    # Utility

    def clear_all(self) -> None:
        """Clear all data from the database."""
        self.repository.clear_db()
