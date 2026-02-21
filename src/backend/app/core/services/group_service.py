import uuid
from _pytest.nodes import Node
from app.core.repository import Repositories

from typing import List, Optional, Set, Tuple

from enum import Enum
from app.core.repository.base_repo import BaseRepo
from app.core.model.nodes import ProjectNode
from app.core.model import StructureGroupNode, CodeElementGroupNode, CallGroupNode
from app.core.model.schemas import StructureGroupSchema, CodeElementGroupSchema, CallGroupSchema


class GroupType(Enum):
    STRUCTURE = "structure_group"
    CODE_ELEMENT = "code_element_group"
    CALL = "call_group"


class GroupService():
    def __init__(self, repos: Repositories, project: ProjectNode):
        self.repos = repos
        self.project = project

    def current_repo(self, group_type: GroupType) -> BaseRepo:
        if group_type == GroupType.STRUCTURE:
            return self.repos.structure_group_repo
        elif group_type == GroupType.CODE_ELEMENT:
            return self.repos.code_element_group_repo
        elif group_type == GroupType.CALL:
            return self.repos.call_group_repo
        else:
            raise ValueError(f"Invalid group type: {group_type}")

    def current_node(self, group_type: GroupType):
        if group_type == GroupType.STRUCTURE:
            return StructureGroupNode
        elif group_type == GroupType.CODE_ELEMENT:
            return CodeElementGroupNode
        elif group_type == GroupType.CALL:
            return CallGroupNode
        else:
            raise ValueError(f"Invalid group type: {group_type}")

    def current_schema(self, group_type: GroupType):
        if group_type == GroupType.STRUCTURE:
            return StructureGroupSchema
        elif group_type == GroupType.CODE_ELEMENT:
            return CodeElementGroupSchema
        elif group_type == GroupType.CALL:
            return CallGroupSchema
        else:
            raise ValueError(f"Invalid group type: {group_type}")

    async def get_children(self, group_id: str, group_type: GroupType, branch_name: Optional[str] = None):
        repo = self.current_repo(group_type)
        return await repo.get_children(group_id, self.project.db_name, branch_name=branch_name)

    async def move_item(self, new_parent_id: str, item_id: str, item_type: str, group_type: GroupType, branch_name: Optional[str] = None):
        repo = self.current_repo(group_type)
        return await repo.move_item(new_parent_id, item_id, item_type, self.project.db_name, branch_name=branch_name)

    async def move_batch(self, moves: List[Tuple[str, str, str]], group_type: GroupType, branch_name: Optional[str] = None):
        repo = self.current_repo(group_type)
        return await repo.move_batch(moves, self.project.db_name, branch_name=branch_name)

    async def create(self, name: str, description: str, parent_id: Optional[str], children: List[Tuple[str, str]], group_type: GroupType, branch_name: Optional[str] = None):
        repo = self.current_repo(group_type)
        node = self.current_node(group_type)
        schema = self.current_schema(group_type)
        group = node(
            id=f"{schema.__name__}/{str(uuid.uuid4())}",
            name=name,
            description=description
        )

        await repo.create(group, self.project.db_name, branch_name=branch_name)

        moves = []
        for child in children:
            moves.append((child[0], group.id, child[1]))
        if parent_id:
            await repo.move_item(parent_id, group.id, group_type.value, self.project.db_name, branch_name=branch_name)
        if moves:
            print(f" moves {moves}")
            await repo.move_batch(moves, self.project.db_name, branch_name=branch_name)

        return group

    async def delete(self, group_id: str, group_type: GroupType, branch_name: Optional[str] = None):
        repo = self.current_repo(group_type)
        return await repo.delete(group_id, project_db_name=self.project.db_name, branch_name=branch_name)
