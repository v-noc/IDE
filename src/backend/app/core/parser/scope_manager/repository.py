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
          
                mro: $mro,
                checksum: $checksum
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

                "mro": scope.mro,
                "checksum": scope.checksum,
            }
        )

    def update_scope(self, scope: ScopeModel) -> None:
        """Update an existing Scope node's properties."""
        self.conn.execute(
            """
            MATCH (s:Scope {id: $id})
            SET s.name = $name,
                s.qname = $qname,
                s.type = $type,
                s.file_path = $file_path,
                s.start_line = $start_line,
                s.start_col = $start_col,
                s.end_line = $end_line,
                s.end_col = $end_col,

                s.mro = $mro,
                s.checksum = $checksum
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

                "mro": scope.mro,
                "checksum": scope.checksum,
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

                mro=node.get("mro", []),
                checksum=node.get("checksum"),
            )
        return None

    def get_scope_by_qname(self, qname: str) -> Optional[ScopeModel]:
        """Get a scope by its qualified name."""
        result = self.conn.execute(
            "MATCH (s:Scope {qname: $qname}) RETURN s",
            {"qname": qname}
        )
        if not result:
            return None
        node = result[0][0]
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

            mro=node.get("mro", []),
            checksum=node.get("checksum"),
        )

    def delete_scope(self, scope_id: str) -> None:
        """Delete a scope and its relationships."""
        self.conn.execute(
            "MATCH (s:Scope {id: $id}) DETACH DELETE s",
            {"id": scope_id}
        )

    def delete_file_scope(self, file_path: str) -> None:
        """Delete a file scope and its children."""
        # Find file scope
        self.conn.execute(
            """
            MATCH (s:Scope {file_path: $file_path, type: 'file'})
            DETACH DELETE s
            """,
            {"file_path": file_path}
        )
        # Note: DETACH DELETE s will remove relationships.
        # But what about children (classes/functions)?
        # They are connected via CONTAINS.
        # If we delete the file scope, the children become orphans?
        # Or should we cascade delete?
        # Usually we want to cascade delete the entire tree under the file.
        # We can use a variable length path or just delete everything with that file_path?
        # Deleting everything with file_path is safer and easier.
        self.conn.execute(
            """
            MATCH (s:Scope {file_path: $file_path})
            DETACH DELETE s
            """,
            {"file_path": file_path}
        )

    def link_parent_child(self, parent_id: str, child_id: str) -> None:
        """Create CONTAINS relationship."""
        self.conn.execute(
            """
            MATCH (p:Scope {id: $parent_id}), (c:Scope {id: $child_id})
            CREATE (p)-[:CONTAINS]->(c)
            """,
            {"parent_id": parent_id, "child_id": child_id}
        )

    def get_children(self, parent_id: str) -> List[ScopeModel]:
        """Get all direct children of a scope."""
        result = self.conn.execute(
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

                mro=node.get("mro", []),
                checksum=node.get("checksum"),
            ))
        return children

    def create_call_site(
        self,
        caller_id: str,
        callee_id: Optional[str],
        call_site: CallSiteModel,
        prev_call_site_id: Optional[str] = None,
    ) -> None:
        """Create a call site node and link it to caller and (optionally) callee."""
        # Create CallSite node
        self.conn.execute(
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
            }
        )

        # Link to Caller
        self.conn.execute(
            """
            MATCH (caller:Scope {id: $caller_id}), (cs:CallSite {id: $cs_id})
            CREATE (caller)-[:HAS_CALL_SITE]->(cs)
            """,
            {"caller_id": caller_id, "cs_id": call_site.id}
        )

        # Link to Callee (if resolved)
        if callee_id:
            self.conn.execute(
                """
                MATCH (cs:CallSite {id: $cs_id}), (callee:Scope {id: $callee_id})
                CREATE (cs)-[:TARGETS]->(callee)
                """,
                {"cs_id": call_site.id, "callee_id": callee_id}
            )

        # Link to previous call site (if chained)
        if prev_call_site_id:
            self.conn.execute(
                """
                MATCH (prev:CallSite {id: $prev_id}), (curr:CallSite {id: $curr_id})
                CREATE (prev)-[:NEXT_IN_CHAIN]->(curr)
                """,
                {"prev_id": prev_call_site_id, "curr_id": call_site.id}
            )

    def clear_calls_from_scope(self, scope_id: str) -> None:
        """Delete all call sites originating from the given scope."""
        self.conn.execute(
            """
            MATCH (s:Scope {id: $id})-[:HAS_CALL_SITE]->(cs:CallSite)
            DETACH DELETE cs
            """,
            {"id": scope_id}
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

                mro=node.get("mro", []),
                checksum=node.get("checksum"),
            ))
        return scopes

    def get_all_file_scopes(self) -> List[ScopeModel]:
        """Get all scopes of type FILE."""
        result = self.conn.execute("MATCH (s:Scope {type: 'file'}) RETURN s")
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

                mro=node.get("mro", []),
                checksum=node.get("checksum"),
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
