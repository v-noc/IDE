from collections import deque
from typing import List, Optional

from .db import DBConnectionManager
from .models import ScopeModel, CallSiteModel


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

    def delete_scope(self, scope_id: str) -> None:
        """Delete a scope and its relationships."""
        scope_ids = self._collect_scope_tree_ids(scope_id)
        if not scope_ids:
            return
        self._delete_scope_nodes(scope_ids)

    def delete_file_scope(self, file_path: str) -> None:
        """Delete a file scope and its children."""
        file_scope_ids = [
            row[0]
            for row in self.conn.execute(
                """
                MATCH (s:Scope {file_path: $file_path, type: 'file'})
                RETURN s.id
                """,
                {"file_path": file_path},
            )
            if row[0]
        ]

        if file_scope_ids:
            for scope_id in file_scope_ids:
                self.delete_scope(scope_id)
            return

        orphan_scope_ids = [
            row[0]
            for row in self.conn.execute(
                """
                MATCH (s:Scope {file_path: $file_path})
                RETURN s.id
                """,
                {"file_path": file_path},
            )
            if row[0]
        ]

        if orphan_scope_ids:
            self._delete_scope_nodes(orphan_scope_ids)

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
        """Create a call site node and link it to caller/callee."""
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
                MATCH (cs:CallSite {id: $cs_id})
                MATCH (callee:Scope {id: $callee_id})
                CREATE (cs)-[:TARGETS]->(callee)
                """,
                {"cs_id": call_site.id, "callee_id": callee_id}
            )

        # Link to previous call site (if chained)
        if prev_call_site_id:
            self.conn.execute(
                """
                MATCH (prev:CallSite {id: $prev_id})
                MATCH (curr:CallSite {id: $curr_id})
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
            MATCH path = (
                start:CallSite {id: $id}
            )-[:NEXT_IN_CHAIN*0..]->(cs:CallSite)
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

    def get_call_chain_roots(
        self,
        target_scope_id: Optional[str] = None,
    ) -> List[CallSiteModel]:
        """
        Get call sites that start a chain (no incoming NEXT_IN_CHAIN).

        If `target_scope_id` is provided, only include roots whose chain
        targets that scope.
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
            roots.append(
                CallSiteModel(
                    id=node["id"],
                    line=node["line"],
                    col=node["col"],
                )
            )
        return roots

    def clear_db(self) -> None:
        """Clear all nodes and relationships."""
        self.conn.execute("MATCH (n) DETACH DELETE n")

    def _collect_scope_tree_ids(self, root_scope_id: str) -> List[str]:
        root_result = self.conn.execute(
            """
            MATCH (root:Scope {id: $id})
            RETURN root.id
            """,
            {"id": root_scope_id},
        )

        root_exists = False
        for row in root_result:
            if row[0]:
                root_exists = True
                break

        if not root_exists:
            return []

        scope_ids: List[str] = []
        queue: deque[str] = deque([root_scope_id])
        seen = set()

        while queue:
            current_id = queue.popleft()
            if current_id in seen:
                continue
            seen.add(current_id)
            scope_ids.append(current_id)

            child_result = self.conn.execute(
                """
                MATCH (parent:Scope {id: $parent_id})
                      -[:CONTAINS]->(child:Scope)
                RETURN child.id
                """,
                {"parent_id": current_id},
            )
            for row in child_result:
                child_id = row[0]
                if child_id and child_id not in seen:
                    queue.append(child_id)

        return scope_ids

    def _delete_scope_nodes(self, scope_ids: List[str]) -> None:
        unique_ids = list({scope_id for scope_id in scope_ids if scope_id})
        for scope_id in unique_ids:
            # Delete call sites owned by this scope
            self.conn.execute(
                """
                MATCH (scope:Scope {id: $id})
                OPTIONAL MATCH (scope)-[:HAS_CALL_SITE]->(cs:CallSite)
                DETACH DELETE cs
                """,
                {"id": scope_id},
            )
            # Delete the scope node itself (DETACH removes relationships)
            self.conn.execute(
                """
                MATCH (scope:Scope {id: $id})
                DETACH DELETE scope
                """,
                {"id": scope_id},
            )
