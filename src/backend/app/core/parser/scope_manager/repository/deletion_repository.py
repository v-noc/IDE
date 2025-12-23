from collections import deque
from typing import List
import asyncio
from ..db import DBConnectionManager


class DeletionRepository:
    """Repository for deletion operations."""

    def __init__(self, db_manager: DBConnectionManager):
        self.conn = db_manager.get_connection()

    async def delete_scope(self, scope_id: str) -> None:
        """Delete a scope and its relationships."""
        scope_ids = await self._collect_scope_tree_ids(scope_id)
        if not scope_ids:
            return
        await self._delete_scope_nodes(scope_ids)

    async def delete_file_scope(self, file_path: str) -> None:
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
            await asyncio.gather(
                *(self.delete_scope(scope_id) for scope_id in file_scope_ids)
            )
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
            await self._delete_scope_nodes(orphan_scope_ids)

    async def _delete_call_sites(self, root_scope_ids: List[str]) -> None:
        await self.conn.execute(
            """
            UNWIND $root_scope_ids AS root_id
            MATCH (root:Scope {id: root_id})
            OPTIONAL MATCH (root)-[:CONTAINS*0..]->(scope:Scope)
            OPTIONAL MATCH (scope)-[:HAS_CALL_SITE]->(cs:CallSite)
            DETACH DELETE cs
            """,
            {"root_scope_ids": root_scope_ids},
        )

    async def _delete_scopes(self, root_scope_ids: List[str]) -> None:
        await self.conn.execute(
            """
            UNWIND $root_scope_ids AS root_id
            MATCH (root:Scope {id: root_id})
            OPTIONAL MATCH (root)-[:CONTAINS*0..]->(scope:Scope)
            DETACH DELETE scope
            """,
            {"root_scope_ids": root_scope_ids},
        )

    async def batch_delete_scopes(self, root_scope_ids: List[str]) -> None:
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
        await self.conn.execute(
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
        await self.conn.execute(
            """
            UNWIND $root_scope_ids AS root_id
            MATCH (root:Scope {id: root_id})
            OPTIONAL MATCH (root)-[:CONTAINS*0..]->(scope:Scope)
            DETACH DELETE scope
            """,
            {"root_scope_ids": root_scope_ids},
        )

    async def batch_delete_file_scopes(self, file_paths: List[str]) -> None:
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
        await self.conn.execute(
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
        await self.conn.execute(
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
        await self.conn.execute(
            """
            UNWIND $file_paths AS file_path
            MATCH (file_scope:Scope {file_path: file_path, type: 'file'})
            OPTIONAL MATCH (file_scope)-[:CONTAINS*0..]->(scope:Scope)
            DETACH DELETE scope
            """,
            {"file_paths": file_paths},
        )

    async def clear_db(self) -> None:
        """Clear all nodes and relationships."""
        await self.conn.execute("MATCH (n) DETACH DELETE n")

    async def _collect_scope_tree_ids(
        self, root_scope_id: str
    ) -> List[str]:
        """Get all scope IDs in tree using single recursive query."""
        result = await self.conn.execute(
            """
            MATCH (root:Scope {id: $id})
            OPTIONAL MATCH (root)-[:CONTAINS*0..]->(scope:Scope)
            RETURN root.id, COLLECT(scope.id) AS descendant_ids
            """,
            {"id": root_scope_id},
        )

        for row in result:
            root_id = row[0]
            descendant_ids = row[1] or []
            if root_id:
                return [root_id] + descendant_ids

        return []

    async def _delete_scope_nodes(self, scope_ids: List[str]) -> None:
        unique_ids = list({scope_id for scope_id in scope_ids if scope_id})
        for scope_id in unique_ids:
            # Delete call sites owned by this scope
            await self.conn.execute(
                """
                MATCH (scope:Scope {id: $id})
                OPTIONAL MATCH (scope)-[:HAS_CALL_SITE]->(cs:CallSite)
                DETACH DELETE cs
                """,
                {"id": scope_id},
            )
            # Delete the scope node itself (DETACH removes relationships)
            await self.conn.execute(
                """
                MATCH (scope:Scope {id: $id})
                DETACH DELETE scope
                """,
                {"id": scope_id},
            )
