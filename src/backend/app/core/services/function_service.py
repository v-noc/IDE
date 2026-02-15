from datetime import datetime, timezone
from typing import Literal, Optional
from app.core.repository import Repositories
from app.core.model.nodes import FunctionNode, ProjectNode
from app.core.model.properties import CodePosition


class FunctionService():
    def __init__(self, repos: Repositories, project: ProjectNode):
        self.repos = repos
        self.project = project

    async def create(self, id: str, name: str, qname: str, description: str, position: CodePosition):
        function = FunctionNode(
            id=id,
            name=name,
            qname=qname,
            description=description,
            code_position=position,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        return await self.repos.function_repo.create(function, self.project.db_name)

    async def get(self, function_id: str):
        return await self.repos.function_repo.get_by_id(function_id, self.project.db_name)

    async def update(self, function: FunctionNode):
        return await self.repos.function_repo.update(function, self.project.db_name)

    async def delete(self, function_key: str):
        return await self.repos.function_repo.delete(function_key, self.project.db_name)

    async def add_child(
        self,
        parent_function_id: str,
        item_id: str,
        item_type: Literal["function", "class", "call", "code_element_group", "call_group"],
    ):
        return await self.repos.function_repo.move_item(
            parent_function_id, item_id, item_type, self.project.db_name
        )

    async def add_function(self, parent_function_id: str, function_id: str):
        return await self.add_child(parent_function_id, function_id, "function")

    async def add_class(self, parent_function_id: str, class_id: str):
        return await self.add_child(parent_function_id, class_id, "class")

    async def add_call(self, parent_function_id: str, call_id: str):
        return await self.add_child(parent_function_id, call_id, "call")

    async def move_item(
        self,
        new_parent_id: str,
        item_id: str,
        item_type: Literal["function", "class", "call", "code_element_group", "call_group"],
    ):
        return await self.repos.function_repo.move_item(
            new_parent_id, item_id, item_type, self.project.db_name
        )

    async def get_children(
        self, function_id: str, child_type: Optional[list[str]] = None
    ):
        return await self.repos.function_repo.get_children(
            function_id, child_type or [], self.project.db_name
        )
