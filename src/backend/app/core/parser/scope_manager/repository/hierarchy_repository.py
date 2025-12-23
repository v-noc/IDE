from typing import List

from ..db import DBConnectionManager
from ..models import ScopeModel


class HierarchyRepository:
    """Repository for hierarchy/parent-child relationship operations."""

    def __init__(self, db_manager: DBConnectionManager):
        self.conn = db_manager.get_connection()

    async def link_parent_child(self, parent_id: str, child_id: str) -> None:
        """Create CONTAINS relationship."""
        await self.conn.execute(
            """
            MATCH (p:Scope {id: $parent_id}), (c:Scope {id: $child_id})
            CREATE (p)-[:CONTAINS]->(c)
            """,
            {"parent_id": parent_id, "child_id": child_id}
        )

    async def batch_link_parent_child(self, relationships: List[dict[str, str]]) -> None:
        """Batch create CONTAINS relationships. relationships is a list of dicts with 'parent_id' and 'child_id' keys."""
        if not relationships:
            return

        await self.conn.execute(
            """
            UNWIND $relationships AS rel
            MATCH (p:Scope {id: rel.parent_id}), (c:Scope {id: rel.child_id})
            CREATE (p)-[:CONTAINS]->(c)
            """,
            {"relationships": relationships}
        )

    async def get_children(self, parent_id: str) -> List[ScopeModel]:
        """Get all direct children of a scope."""
        result = await self.conn.execute(
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
