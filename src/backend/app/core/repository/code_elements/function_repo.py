from typing import Literal, Optional, Union, List, Tuple

from app.core.model.nodes import ClassNode, FunctionNode
from app.core.model.schemas import ClassSchema, FunctionSchema
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


class FunctionRepo(BaseRepo[FunctionNode, FunctionSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, FunctionNode, FunctionSchema)

    @staticmethod
    def _merge_update_fields(existing_raw: dict, _node: FunctionNode, schema: FunctionSchema):
        BaseRepo.merge_set_fields(
            schema, existing_raw, CODE_SET_FIELDS_TO_PRESERVE)

    @staticmethod
    def _merge_class_update_fields(existing_raw: dict, _node: ClassNode, schema: ClassSchema):
        BaseRepo.merge_set_fields(
            schema, existing_raw, CODE_SET_FIELDS_TO_PRESERVE)

    async def create(self, function: Union[FunctionNode, List[FunctionNode]], project_db_name: str, raw: bool = False, branch_name: Optional[str] = None):

        result = await self.create_nodes(
            function,
            project_db_name,
            singular_name="function",
            plural_name="functions",
            raw=raw,
            branch_name=branch_name,
        )
        return result

    async def get_by_id(self, function_id: str, project_db_name: str, raw: bool = False):
        return await super().get_by_id(function_id, project_db_name, raw)

    async def delete(self, function_id: str, project_db_name: str):
        return await self.delete_with_parent_cleanup(
            function_id,
            parent_field="function_children|class_children",
            project_db_name=project_db_name,
            commit_msg=f"Deleting function {function_id}",
        )

    async def delete_batch(self, function_ids: List[str], project_db_name: str):
        return await self.delete_batch_with_parent_cleanup(
            function_ids,
            parent_field="function_children|class_children",
            binding_var="v:function_id",
            project_db_name=project_db_name,
            commit_msg=f"Deleting functions {', '.join(function_ids[:5])}",
        )

    async def update(self, function: FunctionNode, project_db_name: str):
        return await self.update_node(
            function,
            project_db_name=project_db_name,
            commit_msg=f"Updating function {function.id}",
            update_schema=self._merge_update_fields,
        )

    async def update_batch(
        self,
        nodes: List[Union[FunctionNode, ClassNode]],
        project_db_name: str,
    ):
        """Update functions and/or classes in a single batch request."""
        if not nodes:
            return True

        async with self.session(project_db_name) as new_client:
            try:
                items_raw = await new_client.get_documents([n.id for n in nodes])
            except Exception as exc:
                print(exc)
                return None

        id_to_raw = {r["@id"]: r for r in items_raw}
        schemas = []

        for node in nodes:
            existing_raw = id_to_raw.get(node.id)
            if not existing_raw:
                continue

            if isinstance(node, FunctionNode):
                schema = FunctionSchema.from_pydantic(node)
                self._merge_update_fields(existing_raw, node, schema)
            else:
                schema = ClassSchema.from_pydantic(node)
                self._merge_class_update_fields(existing_raw, node, schema)

            BaseRepo.touch_updated_at(schema)
            schemas.append(schema)

        if not schemas:
            return None

        async with self.session(project_db_name) as new_client:
            try:
                await new_client.update_document(
                    schemas,
                    commit_msg=f"Updating {len(schemas)} code elements (functions and classes)",
                )
            except Exception as exc:
                print(exc)
                return False
        return True

    async def get_children(
        self, function_id: str, child_type: list[str], project_db_name: str
    ):
        field_name = build_path_field_name(
            child_type, CODE_ELEMENT_FIELDS, type_to_field=CODE_CHILD_TYPE_TO_FIELD
        )
        return await self.get_children_by_path(
            function_id,
            field_name,
            parse_code_element_child,
            project_db_name,
            allowed_path_fields=CODE_ELEMENT_FIELDS,
        )

    async def move_item(
        self,
        new_parent_id: str,
        item_id: str,
        item_type: Literal[
            "function", "class", "call", "code_element_group", "call_group"
        ],
        project_db_name: str,
    ):
        return await self.move_item_by_type(
            new_parent_id,
            item_id,
            item_type,
            child_type_to_field=CODE_CHILD_TYPE_TO_FIELD,
            project_db_name=project_db_name,
        )

    async def move_batch(self, moves: List[Tuple[str, str, str]], project_db_name: str):
        return await self.move_batch_by_type(
            moves,
            child_type_to_field=CODE_CHILD_TYPE_TO_FIELD,
            project_db_name=project_db_name,
        )
