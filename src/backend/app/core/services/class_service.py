from datetime import datetime, timezone
from typing import Literal, Optional

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
        base_classes: Optional[set] = None,
    ):
        class_node = ClassNode(
            id=id,
            name=name,
            qname=qname,
            description=description,
            base_classes=base_classes or set(),
            code_position=position,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        return await self.repos.class_repo.create(class_node, self.project.db_name)

    async def get(self, class_id: str):
        return await self.repos.class_repo.get_by_id(
            class_id, self.project.db_name
        )

    async def update(self, class_node: ClassNode):
        return await self.repos.class_repo.update(
            class_node, self.project.db_name
        )

    async def delete(self, class_id: str):
        return await self.repos.class_repo.delete(
            class_id, self.project.db_name
        )

    async def add_child(
        self,
        parent_class_id: str,
        item_id: str,
        item_type: Literal[
            "function", "class", "call", "code_element_group", "call_group"
        ],
    ):
        return await self.repos.class_repo.move_item(
            parent_class_id, item_id, item_type, self.project.db_name
        )

    async def add_function(self, parent_class_id: str, function_id: str):
        return await self.add_child(parent_class_id, function_id, "function")

    async def add_call(self, parent_class_id: str, call_id: str):
        return await self.add_child(parent_class_id, call_id, "call")

    async def add_class(self, parent_class_id: str, class_id: str):
        return await self.add_child(parent_class_id, class_id, "class")

    async def move_item(
        self,
        new_parent_id: str,
        item_id: str,
        item_type: Literal[
            "function", "class", "call", "code_element_group", "call_group"
        ],
    ):
        return await self.repos.class_repo.move_item(
            new_parent_id, item_id, item_type, self.project.db_name
        )

    async def get_children(
        self, class_id: str, child_type: Optional[list[str]] = None
    ):
        return await self.repos.class_repo.get_children(
            class_id, child_type or [], self.project.db_name
        )
