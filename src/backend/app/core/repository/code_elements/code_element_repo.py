from typing import Union, List, Tuple
from terminusdb_client.woqlquery.woql_query import Doc, WOQLQuery as WQ

from app.core.model.nodes import ClassNode, FunctionNode
from app.core.model.schemas import ClassSchema, FunctionSchema
from app.core.repository.base_repo import BaseRepo
from app.core.repository.utils import (
    CODE_CHILD_TYPE_TO_FIELD,
    CODE_ELEMENT_FIELDS,
    CODE_SET_FIELDS_TO_PRESERVE,
    build_path_field_name,
    parse_code_element_child,
)
from app.db.async_terminus_client import AsyncClient

# Define a type for elements handled here
CodeNode = Union[FunctionNode, ClassNode]
CodeSchema = Union[FunctionSchema, ClassSchema]


class CodeElementRepo(BaseRepo[CodeNode, CodeSchema]):
    def __init__(self, client: AsyncClient):
        # We pass FunctionNode as default, but methods handle both
        super().__init__(client, FunctionNode, FunctionSchema)

    @staticmethod
    def _merge_update_fields(existing_raw: dict, _node: CodeNode, schema: CodeSchema):
        BaseRepo.merge_set_fields(
            schema, existing_raw, CODE_SET_FIELDS_TO_PRESERVE)

    def _to_schema(self, node: CodeNode) -> CodeSchema:
        if isinstance(node, FunctionNode):
            return FunctionSchema.from_pydantic(node)
        elif isinstance(node, ClassNode):
            return ClassSchema.from_pydantic(node)
        else:
            raise ValueError(f"Invalid node type: {type(node)}")

    async def update(self, node: CodeNode):
        return await self.update_node(
            node,
            commit_msg=f"Updating code element {node.id}",
            update_schema=self._merge_update_fields,
        )

    async def create(self, node: Union[CodeNode, List[CodeNode]], raw: bool = False):
        return await self.create_nodes(
            node,
            singular_name="code element",
            plural_name="code elements",
            raw=raw,
        )

    async def update_batch(self, nodes: List[CodeNode]):
        """Polymorphic update for both Classes and Functions."""
        if not nodes:
            return True

        items_raw = await self.get_by_ids([n.id for n in nodes], raw=True)
        id_to_raw = {r["@id"]: r for r in items_raw} if items_raw else {}

        schemas = []
        for node in nodes:
            existing_raw = id_to_raw.get(node.id)
            if not existing_raw:
                continue

            # Determine correct schema class
            schema_cls = FunctionSchema if isinstance(
                node, FunctionNode) else ClassSchema
            schema = schema_cls.from_pydantic(node)

            self._merge_update_fields(existing_raw, node, schema)
            self.touch_updated_at(schema)
            schemas.append(schema)

        if not schemas:
            return None
        return await self.client.update_document(schemas, commit_msg=f"Updating {len(schemas)} elements")

    async def delete(self, item_id: str):
        # Cleans up both possible parent link fields
        return await self.delete_with_parent_cleanup(
            item_id,
            parent_field="function_children|class_children",
            commit_msg=f"Deleting code element {item_id}",
        )

    async def get_children(self, parent_id: str, child_types: list[str]):
        field_name = build_path_field_name(
            child_types, CODE_ELEMENT_FIELDS, type_to_field=CODE_CHILD_TYPE_TO_FIELD
        )
        return await self.get_children_by_path(
            parent_id,
            field_name,
            parse_code_element_child,
            allowed_path_fields=CODE_ELEMENT_FIELDS,
        )

    async def move_item(self, new_parent_id: str, item_id: str, child_type: str):
        return await self.move_item_by_type(
            new_parent_id,
            item_id,
            child_type,
            child_type_to_field=CODE_CHILD_TYPE_TO_FIELD,
        )

    async def move_batch(self, moves: List[Tuple[str, str, str]]):
        return await self.move_batch_by_type(moves, child_type_to_field=CODE_CHILD_TYPE_TO_FIELD)

    async def flush_batch(self, insert: List[FunctionNode | ClassNode], update: List[FunctionNode | ClassNode], delete: List[str], move: List[Tuple[str, str, str]]):
        if not insert and not update and not delete and not move:
            return True

        queries = []

        for node in insert:

            if isinstance(node, FunctionNode):
                schema = FunctionSchema.from_pydantic(node)._obj_to_dict()[0]
            elif isinstance(node, ClassNode):
                schema = ClassSchema.from_pydantic(node)._obj_to_dict()[0]

            else:
                raise ValueError(f"Invalid node type: {type(node)}")

            queries.append(WQ().insert_document(Doc(schema)))

        # build delete operations
        for delete_id in delete:
            field = "function_children"
            if delete_id.startswith("ClassSchema"):
                field = "class_children"
            queries.append(WQ().woql_and(
                WQ().opt(
                    WQ().triple("v:parent", field, delete_id)
                    .delete_triple("v:parent", field, delete_id)
                ),
                WQ().delete_document(delete_id)
            ))
            # build insert operations

        # for node in update:
            # queries.append(q)

        for item_id, new_parent_id, child_type in move:
            field = CODE_CHILD_TYPE_TO_FIELD.get(
                child_type, "function_children")

            is_new_item = False
            for node in insert:
                if node.id == item_id:
                    is_new_item = True
                    break
            if is_new_item:
                queries.append(WQ().add_triple(new_parent_id, field, item_id))
            else:
                queries.append(WQ().woql_and(
                    WQ().opt(
                        WQ().triple("v:old_parent", field, item_id)
                        .delete_triple("v:old_parent", field, item_id)
                    ),
                    WQ().add_triple(new_parent_id, field, item_id)
                ))

        if not queries:
            return True

        combined = WQ().woql_and(*queries)

        try:
            result = await self.client.query(combined, commit_msg=f"Batch: {len(insert)} inserts, {len(delete)} deletes, {len(move)} moves")
            print(result)
            return True
        except Exception as exc:
            print(f"Batch operation failed: {exc}")
            return False
