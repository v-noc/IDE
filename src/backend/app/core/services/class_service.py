from datetime import datetime, timezone

from app.core.repository import Repositories
from app.core.model.nodes import ClassNode
from app.core.model.properties import CodePosition
from app.core.model.nodes import ProjectNode


class ClassService():
    def __init__(self, repos: Repositories, project: ProjectNode):
        self.repos = repos
        self.project = project

    async def create(
        self,
        id: str,
        name: str,
        qname: str,
        description: str,
        position: CodePosition,

    ):
        class_node = ClassNode(
            id=id,
            name=name,
            qname=qname,
            description=description,
            implements=[qname],
            code_position=position,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        return await self.repos.class_repo.create(class_node, self.project.db_name)

    async def get(self, class_id: str):
        return await self.repos.class_repo.get_by_id(class_id)

    async def update(self, class_node: ClassNode):
        return await self.repos.class_repo.update(class_node.key, class_node)

    async def delete(self, class_key: str):
        return await self.delete_recursive(class_key)

    async def add_function(self, parent_class_id: str, function_id: str):
        return await self.add_child(parent_class_id, function_id)

    async def add_call(self, parent_class_id: str, call_id: str):
        return await self.add_child(parent_class_id, call_id)

    async def add_class(self, parent_class_id: str, class_id: str):
        return await self.add_child(parent_class_id, class_id)

    async def get_children(self, class_id: str):
        return await self.repos.class_repo.get_containment_tree(class_id)
