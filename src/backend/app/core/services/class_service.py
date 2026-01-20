from typing import Optional
from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import ClassNode
from app.core.model.properties import CodePosition


class ClassService(ContainerService):
    def __init__(self, repos: Repositories):
        super().__init__(repos)

    async def create(
        self,
        name: str,
        qname: str,
        description: str,
        position: CodePosition,
        _key: Optional[str] = None,
    ):
        class_node = ClassNode(
            name=name,
            qname=qname,
            description=description,
            implements=[qname],
            position=position,
        )
        if _key:
            class_node.key = _key
        return await self.repos.class_repo.create(class_node)

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

