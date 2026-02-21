from typing import Literal, Optional, Union, List, Tuple

from app.core.model.nodes import ClassNode
from app.core.model.schemas import ClassSchema
from app.core.repository.base_repo import BaseRepo
from app.core.repository.utils import (
    CODE_CHILD_TYPE_TO_FIELD,
    CODE_ELEMENT_FIELDS,
    CODE_OPTIONAL_FIELDS_TO_PRESERVE,
    CODE_SET_FIELDS_TO_PRESERVE,
    build_path_field_name,
    parse_code_element_child,
)
from app.db.async_terminus_client import AsyncClient


class ClassRepo(BaseRepo[ClassNode, ClassSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, ClassNode, ClassSchema)

    @staticmethod
    def _merge_update_fields(existing_raw: dict, _node: ClassNode, schema: ClassSchema):
        BaseRepo.merge_set_fields(
            schema, existing_raw, CODE_SET_FIELDS_TO_PRESERVE)

    async def create(self, class_node: Union[ClassNode, List[ClassNode]], project_db_name: str, raw: bool = False, branch_name: Optional[str] = None):
        result = await self.create_nodes(
            class_node,
            project_db_name,
            singular_name="class",
            plural_name="classes",
            raw=raw,
            branch_name=branch_name,
        )
        return result

    async def update_batch(self, classes: List[ClassNode], project_db_name: str, branch_name: Optional[str] = None):
        return await self.update_nodes(
            classes,
            project_db_name=project_db_name,
            commit_msg=f"Updating classes {len(classes)}",
            update_schema=self._merge_update_fields,
            branch_name=branch_name,
        )

    async def get_by_id(self, class_id: str, project_db_name: str, raw: bool = False, branch_name: Optional[str] = None):
        return await super().get_by_id(class_id, project_db_name, raw=raw, branch_name=branch_name)

    async def delete(self, class_id: str, project_db_name: str, branch_name: Optional[str] = None):
        return await self.delete_with_parent_cleanup(
            class_id,
            parent_field="class_children|function_children",
            project_db_name=project_db_name,
            commit_msg=f"Deleting class {class_id}",
            branch_name=branch_name,
        )

    async def update(self, class_node: ClassNode, project_db_name: str, branch_name: Optional[str] = None):
        return await self.update_node(
            class_node,
            project_db_name=project_db_name,
            commit_msg=f"Updating class {class_node.id}",
            update_schema=self._merge_update_fields,
            branch_name=branch_name,
        )

    async def get_children(
        self, class_id: str, child_type: list[str], project_db_name: str, branch_name: Optional[str] = None
    ):
        field_name = build_path_field_name(
            child_type, CODE_ELEMENT_FIELDS, type_to_field=CODE_CHILD_TYPE_TO_FIELD
        )
        return await self.get_children_by_path(
            class_id,
            field_name,
            parse_code_element_child,
            project_db_name,
            allowed_path_fields=CODE_ELEMENT_FIELDS,
            branch_name=branch_name,
        )

    async def move_item(
        self,
        new_parent_id: str,
        item_id: str,
        item_type: Literal[
            "function", "class", "call", "code_element_group", "call_group"
        ],
        project_db_name: str,
        branch_name: Optional[str] = None,
    ):
        return await self.move_item_by_type(
            new_parent_id,
            item_id,
            item_type,
            child_type_to_field=CODE_CHILD_TYPE_TO_FIELD,
            project_db_name=project_db_name,
            branch_name=branch_name,
        )

    async def move_batch(self, moves: List[Tuple[str, str, str]], project_db_name: str, branch_name: Optional[str] = None):
        return await self.move_batch_by_type(
            moves,
            child_type_to_field=CODE_CHILD_TYPE_TO_FIELD,
            project_db_name=project_db_name,
            branch_name=branch_name,
        )
