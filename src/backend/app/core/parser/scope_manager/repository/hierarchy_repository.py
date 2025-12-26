import gc
from typing import List

from ..db import DBConnectionManager
from ..models import ScopeModel


class HierarchyRepository:
    """Repository for hierarchy/parent-child relationship operations."""

    def __init__(self, db_manager: DBConnectionManager):
        self.db_manager = db_manager

    async def link_parent_child(self, parent_id: str, child_id: str) -> None:
        """Create CONTAINS relationship."""
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                MATCH (p:Scope {id: $parent_id}), (c:Scope {id: $child_id})
                CREATE (p)-[:CONTAINS]->(c)
                """,
                {"parent_id": parent_id, "child_id": child_id},
            )
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def relink_parent_child(self, new_parent_id: str, child_id: str) -> None:
        """
        Ensure the child has exactly one parent by removing any existing incoming
        CONTAINS relationships, then creating a new one from new_parent_id.
        """
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                MATCH (c:Scope {id: $child_id})
                OPTIONAL MATCH (:Scope)-[r:CONTAINS]->(c)
                DELETE r
                WITH c
                MATCH (p:Scope {id: $new_parent_id})
                CREATE (p)-[:CONTAINS]->(c)
                """,
                {"new_parent_id": new_parent_id, "child_id": child_id},
            )
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def batch_link_parent_child(
        self, relationships: List[dict[str, str]]
    ) -> None:
        """
        Batch create CONTAINS relationships.
        relationships is a list of dicts with 'parent_id' and 'child_id' keys.
        """
        if not relationships:
            return

        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                UNWIND $relationships AS rel
                MATCH (p:Scope {id: rel.parent_id}),
                      (c:Scope {id: rel.child_id})
                CREATE (p)-[:CONTAINS]->(c)
                """,
                {"relationships": relationships},
            )
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def batch_relink_parent_child(
        self, relationships: List[dict[str, str]]
    ) -> None:
        """
        Batch relink CONTAINS relationships.
        For each child_id, remove any incoming CONTAINS edges and create a new one
        from parent_id.
        """
        if not relationships:
            return

        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                UNWIND $relationships AS rel
                MATCH (c:Scope {id: rel.child_id})
                OPTIONAL MATCH (:Scope)-[r:CONTAINS]->(c)
                DELETE r
                WITH rel, c
                MATCH (p:Scope {id: rel.parent_id})
                CREATE (p)-[:CONTAINS]->(c)
                """,
                {"relationships": relationships},
            )
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def get_children(self, parent_id: str) -> List[ScopeModel]:
        """Get all direct children of a scope."""
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                MATCH (p:Scope {id: $parent_id})-[:CONTAINS]->(c:Scope)
                RETURN c
                """,
                {"parent_id": parent_id},
            )
            children = []
            for row in result:
                node = row[0]
                children.append(
                    ScopeModel(
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
                        parent_id=parent_id  # We know the parent here
                    )
                )
            return children
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def get_descendants(self, root_id: str) -> List[ScopeModel]:
        """Get all descendants of a scope (recursive children)."""
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                MATCH (root:Scope {id: $root_id})-[:CONTAINS*]->(c:Scope)
                OPTIONAL MATCH (p:Scope)-[:CONTAINS]->(c)
                RETURN c, p.id as parent_id
                """,
                {"root_id": root_id},
            )
            children = []
            for row in result:
                node = row[0]
                parent_id = row[1]
                children.append(
                    ScopeModel(
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
                        parent_id=parent_id
                    )
                )
            return children
        finally:
            if result is not None:
                del result
                gc.collect()

