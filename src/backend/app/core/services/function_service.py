from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import FunctionNode
from app.core.model.properties import CodePosition
from typing import Optional


class FunctionService(ContainerService):
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
        function = FunctionNode(
            name=name,
            qname=qname,
            description=description,
            position=position,
        )
        if _key:
            function.key = _key
        return await self.repos.function_repo.create(function)

    async def get(self, function_id: str):
        return await self.repos.function_repo.get_by_id(function_id)

    async def update(self, function: FunctionNode):
        return await self.repos.function_repo.update(function.key, function)

    async def delete(self, function_key: str):
        return await self.delete_recursive(function_key)

    async def add_function(self, parent_function_id: str, function_id: str):
        return await self.add_child_to_container(parent_function_id, function_id)

    async def add_call(self, parent_function_id: str, call_id: str):
        return await self.add_child_to_container(parent_function_id, call_id)

    async def add_class(self, parent_function_id: str, class_id: str):
        return await self.add_child_to_container(parent_function_id, class_id)


    async def get_children(self, function_id: str):
        return await self.repos.function_repo.get_containment_tree(function_id)

