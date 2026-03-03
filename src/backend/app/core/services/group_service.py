import uuid
from app.core.repository import Repositories

from typing import List, Optional, Tuple

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

    async def move_item(self, new_parent_id: Optional[str], item_id: str, item_type: str, group_type: GroupType, branch_name: Optional[str] = None):
        repo = self.current_repo(group_type)
        return await repo.move_item(new_parent_id, item_id, item_type, self.project.db_name, branch_name=branch_name)

    async def move_batch(self, moves: List[Tuple[str, str, str]], group_type: GroupType, branch_name: Optional[str] = None):
        repo = self.current_repo(group_type)
        return await repo.move_batch(moves, self.project.db_name, branch_name=branch_name)

    async def create(self, name: str, description: str, parent_id: Optional[str], children: List[Tuple[str, str]], group_type: GroupType,  branch_name: Optional[str] = None):
        """Create group and move children in a single transaction. If creation fails, no items are moved."""
        repo = self.current_repo(group_type)
        node = self.current_node(group_type)
        schema = self.current_schema(group_type)
        group = node(
            id=f"{schema.__name__}/{str(uuid.uuid4())}",
            name=name,
            description=description
        )

        success = await repo.create_and_move_items(
            group,
            items=children,
            project_db_name=self.project.db_name,
            branch_name=branch_name,
            parent_id=parent_id,
        )
        if not success:
            return None

        return group

    async def update_basic_info(
        self,
        group_id: str,
        group_type: GroupType,
        name: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        branch_name: Optional[str] = None,
    ):
        repo = self.current_repo(group_type)
        node_class = self.current_node(group_type)
        existing_raw = await repo.get_by_id(group_id, self.project.db_name, raw=True)
        if not existing_raw:
            return None
        node = node_class.from_raw_dict(existing_raw)
        if name is not None:
            node.name = name
        if description is not None:
            node.description = description
        return await repo.update(node, self.project.db_name, branch_name=branch_name)

    async def add_child_to_group(
        self,
        group_id: str,
        child_id: str,
        item_type: str,
        group_type: GroupType,
        branch_name: Optional[str] = None,
    ):
        return await self.move_item(group_id, child_id, item_type, group_type, branch_name=branch_name)

    async def remove_child_from_group(
        self,
        group_id: str,
        child_id: str,
        item_type: str,
        new_parent_id: Optional[str],
        group_type: GroupType,
        branch_name: Optional[str] = None,
    ):
        return await self.move_item(new_parent_id, child_id, item_type, group_type, branch_name=branch_name)

    async def delete(self, group_id: str, group_type: GroupType, branch_name: Optional[str] = None):
        repo = self.current_repo(group_type)
        return await repo.delete(group_id, project_db_name=self.project.db_name, branch_name=branch_name)
