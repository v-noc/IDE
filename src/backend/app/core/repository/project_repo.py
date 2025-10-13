

from app.core.model.nodes import ProjectNode
from app.core.repository.base.node_repo import NodeRepository
from arango.database import StandardDatabase


class ProjectRepo(NodeRepository[ProjectNode]):
    """Repository for project collections."""

    def __init__(self, db: StandardDatabase):
        super().__init__(db, "nodes", ProjectNode)

    def get_all_projects(self):
        return self.find({"node_type": "project"})
