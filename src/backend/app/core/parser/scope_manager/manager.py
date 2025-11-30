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
        mro: List[str] = None,
        scope_id: Optional[str] = None,
        checksum: Optional[str] = None,
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
            mro=mro or [],
            checksum=checksum,
        )
        self.repository.create_scope(scope)
        return scope

    def update_scope(self, scope: ScopeModel) -> ScopeModel:
        """Update an existing scope."""
        self.repository.update_scope(scope)
        return scope

    def get_scope(self, scope_id: str) -> Optional[ScopeModel]:
        """Get a scope by ID."""
        return self.repository.get_scope_by_id(scope_id)

    def get_scope_by_qname(self, qname: str) -> Optional[ScopeModel]:
        """Get a scope by qualified name."""
        return self.repository.get_scope_by_qname(qname)

    def delete_scope(self, scope_id: str) -> None:
        """Delete a scope and its relationships."""
        self.repository.delete_scope(scope_id)

    def delete_file_scope(self, file_path: str) -> None:
        """Delete a file scope by its path."""
        self.repository.delete_file_scope(file_path)

    def get_all_scopes(self) -> List[ScopeModel]:
        """Get all scopes."""
        return self.repository.get_all_scopes()

    def get_all_file_scopes(self) -> List[ScopeModel]:
        """Get all scopes of type FILE."""
        return self.repository.get_all_file_scopes()

    def get_all_folder_scopes(self) -> List[ScopeModel]:
        """Get all scopes of type FOLDER."""
        return self.repository.get_all_folder_scopes()

    # Hierarchy Management

    def link_parent_child(self, parent_id: str, child_id: str) -> None:
        """Link a parent scope to a child scope (e.g., Class contains Function)."""
        self.repository.link_parent_child(parent_id, child_id)

    def get_children(self, parent_id: str) -> List[ScopeModel]:
        """Get all children of a scope."""
        return self.repository.get_children(parent_id)

    # Call Site Management

    def create_call(
        self,
        caller_id: str,
        line: int,
        col: int,
        name: Optional[str] = None,
        callee_id: Optional[str] = None,
        prev_call_site_id: Optional[str] = None,
    ) -> CallSiteModel:
        """Create a call site linking caller to callee (if resolved), optionally chained."""
        call_site = CallSiteModel(
            id=str(uuid.uuid4()),
            line=line,
            col=col,
            name=name,
        )
        self.repository.create_call_site(
            caller_id, callee_id, call_site, prev_call_site_id)
        return call_site

    def get_calls_from(self, caller_id: str) -> List[dict]:
        """Get all calls made from a scope (including unresolved callees)."""
        result = self.repository.conn.execute(
            """
            MATCH (caller:Scope {id: $caller_id})-[:HAS_CALL_SITE]->(cs:CallSite)
            OPTIONAL MATCH (cs)-[:TARGETS]->(callee:Scope)
            RETURN cs, callee
            """,
            {"caller_id": caller_id}
        )

        calls = []
        for row in result:
            cs_node = row[0]
            callee_node = row[1] if len(row) > 1 else None

            callee = None
            if callee_node:
                callee = ScopeModel(
                    id=callee_node["id"],
                    name=callee_node["name"],
                    qname=callee_node["qname"],
                    type=callee_node["type"],
                    file_path=callee_node["file_path"],
                    start_line=callee_node["start_line"],
                    start_col=callee_node["start_col"],
                    end_line=callee_node["end_line"],
                    end_col=callee_node["end_col"],
                    mro=callee_node.get("mro", []),
                )

            calls.append({
                "call_site": CallSiteModel(
                    id=cs_node["id"],
                    line=cs_node["line"],
                    col=cs_node["col"],
                    name=cs_node.get("name"),
                ),
                "callee": callee,
            })
        return calls

    def get_call_chain_children(self, call_site_id: str) -> List[dict]:
        """Get NEXT_IN_CHAIN children for a call site, plus their target scope."""
        result = self.repository.conn.execute(
            """
            MATCH (cs:CallSite {id: $call_site_id})-[:NEXT_IN_CHAIN]->(child:CallSite)
            OPTIONAL MATCH (child)-[:TARGETS]->(callee:Scope)
            RETURN child, callee
            """,
            {"call_site_id": call_site_id}
        )

        children = []
        for row in result:
            child_node = row[0]
            callee_node = row[1] if len(row) > 1 else None

            callee = None
            if callee_node:
                callee = ScopeModel(
                    id=callee_node["id"],
                    name=callee_node["name"],
                    qname=callee_node["qname"],
                    type=callee_node["type"],
                    file_path=callee_node["file_path"],
                    start_line=callee_node["start_line"],
                    start_col=callee_node["start_col"],
                    end_line=callee_node["end_line"],
                    end_col=callee_node["end_col"],
                    mro=callee_node.get("mro", []),
                )

            children.append({
                "call_site": CallSiteModel(
                    id=child_node["id"],
                    line=child_node["line"],
                    col=child_node["col"],
                    name=child_node.get("name"),
                ),
                "callee": callee,
            })
        return children

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
                    name=cs_node.get("name"),
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
                    mro=caller_node.get("mro", []),
                ),
            })
        return calls

    def get_call_chain(self, call_site_id: str) -> List[CallSiteModel]:
        """Get the full call chain starting from a call site."""
        return self.repository.get_call_chain(call_site_id)

    def get_call_chain_roots(self, target_scope_id: Optional[str] = None) -> List[CallSiteModel]:
        """
        Get all call sites that are roots of call chains.

        If `target_scope_id` is provided, only return those root call sites for which
        there exists a path along `NEXT_IN_CHAIN` that contains a call site targeting
        the given scope.
        """
        return self.repository.get_call_chain_roots(target_scope_id)

    def clear_calls(self, scope_id: str) -> None:
        """Clear all calls originating from a scope."""
        self.repository.clear_calls_from_scope(scope_id)

    # Utility

    def clear_all(self) -> None:
        """Clear all data from the database."""
        self.repository.clear_db()
