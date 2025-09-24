

from typing import List, Optional
from backend.app.core.model.nodes import ProjectNode
from backend.app.core.repository.base.node_repo import NodeRepository
from backend.app.models.properties import ThemeConfig


class ProjectRepo(NodeRepository[ProjectNode]):
    """Repository for project collections."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_all_projects(self):
        return self.find({"node_type": "project"})
