

from app.core.model.nodes import ProjectNode
from .base.base_node_repo import BaseNodeRepository
from arangoasync.database import AsyncDatabase


class ProjectRepo(BaseNodeRepository[ProjectNode]):
    """Repository for project collections."""

    def __init__(self, db: AsyncDatabase):
        super().__init__(db, "nodes", ProjectNode)

    async def get_all_projects(self):
        return await self.find({"node_type": "project"})

    async def delete(self, key: str) -> bool:
        """Deletes a project and all its children (cascade)."""
        try:
            # Build the start vertex id, e.g. "nodes/<key>"
            start_node_id = f"{self.collection_name}/{key}"

            # Use the shared cascade delete method
            result = await self.cascade_delete(start_node_id, max_depth=50)

            # Return True if any vertices were deleted (including the start node)
            return result.get("removed_vertices", 0) > 0
        except Exception as e:
            print(f"Cascade project delete failed: {e}")
            return False
