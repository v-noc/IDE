from collections import deque
from typing import List

from ..db import DBConnectionManager


class DeletionRepository:
    """Repository for deletion operations."""

    def __init__(self, db_manager: DBConnectionManager):
        self.conn = db_manager.get_connection()

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

    def batch_delete_scopes(self, root_scope_ids: List[str]) -> None:
        """
        Batch delete multiple scopes and all their children/relationships.
        Uses recursive pattern matching to delete entire subtrees without
        collecting IDs first.

        Args:
            root_scope_ids: List of root scope IDs to delete (each will delete
                          its entire subtree)
        """
        if not root_scope_ids:
            return

        # Delete all call sites for root scopes and all their descendants
        # Using variable-length path pattern to match entire subtree
        self.conn.execute(
            """
            UNWIND $root_scope_ids AS root_id
            MATCH (root:Scope {id: root_id})
            OPTIONAL MATCH (root)-[:CONTAINS*0..]->(scope:Scope)
            OPTIONAL MATCH (scope)-[:HAS_CALL_SITE]->(cs:CallSite)
            DETACH DELETE cs
            """,
            {"root_scope_ids": root_scope_ids},
        )

        # Delete all scope nodes and their relationships recursively
        # Using variable-length path pattern to match entire subtree
        self.conn.execute(
            """
            UNWIND $root_scope_ids AS root_id
            MATCH (root:Scope {id: root_id})
            OPTIONAL MATCH (root)-[:CONTAINS*0..]->(scope:Scope)
            DETACH DELETE scope
            """,
            {"root_scope_ids": root_scope_ids},
        )

    def batch_delete_file_scopes(self, file_paths: List[str]) -> None:
        """
        Batch delete multiple file scopes and all their children/relationships.
        Uses recursive pattern matching to delete entire subtrees without
        collecting IDs first.

        Args:
            file_paths: List of file paths to delete
        """
        if not file_paths:
            return

        # Delete all call sites for file scopes and all their descendants
        # Using variable-length path pattern to match entire subtree
        self.conn.execute(
            """
            UNWIND $file_paths AS file_path
            MATCH (file_scope:Scope {file_path: file_path, type: 'file'})
            OPTIONAL MATCH (file_scope)-[:CONTAINS*0..]->(scope:Scope)
            OPTIONAL MATCH (scope)-[:HAS_CALL_SITE]->(cs:CallSite)
            DETACH DELETE cs
            """,
            {"file_paths": file_paths},
        )

        # Delete orphan scopes (scopes with matching file_path but not type 'file')
        # These don't have children, so we can delete them directly
        self.conn.execute(
            """
            UNWIND $file_paths AS file_path
            MATCH (orphan:Scope {file_path: file_path})
            WHERE orphan.type <> 'file'
            OPTIONAL MATCH (orphan)-[:HAS_CALL_SITE]->(cs:CallSite)
            DETACH DELETE cs, orphan
            """,
            {"file_paths": file_paths},
        )

        # Delete all file scope nodes and their relationships recursively
        # Using variable-length path pattern to match entire subtree
        self.conn.execute(
            """
            UNWIND $file_paths AS file_path
            MATCH (file_scope:Scope {file_path: file_path, type: 'file'})
            OPTIONAL MATCH (file_scope)-[:CONTAINS*0..]->(scope:Scope)
            DETACH DELETE scope
            """,
            {"file_paths": file_paths},
        )

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

