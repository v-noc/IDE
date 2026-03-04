from terminusdb_client.woqlquery.woql_query import Doc
from app.core.repository.base_repo import WQ, BaseRepo
from app.db.async_terminus_client import AsyncClient
from app.core.model.nodes import CodeElementGroupNode
from app.core.model.schemas import CodeElementGroupSchema
from typing import List, Literal, Optional, Tuple

from app.core.repository.utils import CODE_CHILD_TYPE_TO_FIELD, CODE_ELEMENT_FIELDS, CODE_SET_FIELDS_TO_PRESERVE, parse_code_element_child


class CodeElementGroupRepo(BaseRepo[CodeElementGroupNode, CodeElementGroupSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, CodeElementGroupNode, CodeElementGroupSchema)

    async def create(self, code_element_group: CodeElementGroupNode, raw: bool = False):
        return await self.create_nodes(
            code_element_group,
            singular_name="code_element_group",
            plural_name="code_element_groups",
            raw=raw,
        )

    async def move_item(
        self,
        new_parent_id: str,
        item_id: str,
        item_type: Literal[
            "function", "class", "call", "code_element_group", "call_group"
        ],
    ):
        return await self.move_item_by_type(
            new_parent_id,
            item_id,
            item_type,
            child_type_to_field=CODE_CHILD_TYPE_TO_FIELD,
        )

    async def move_batch(self, moves: List[Tuple[str, str, str]]):
        return await self.move_batch_by_type(
            moves,
            child_type_to_field=CODE_CHILD_TYPE_TO_FIELD,
        )

    async def get_children(self, group_id: str):
        return await self.get_children_by_path(
            group_id,
            "code_element_group_children",
            parse_code_element_child,
            allowed_path_fields=CODE_ELEMENT_FIELDS,
        )

    @staticmethod
    def _merge_update_fields(existing_raw: dict, _node: CodeElementGroupNode, schema: CodeElementGroupSchema):
        BaseRepo.merge_set_fields(
            schema, existing_raw, CODE_SET_FIELDS_TO_PRESERVE)

    async def update(self, code_element_group: CodeElementGroupNode):
        return await self.update_node(
            code_element_group,
            commit_msg=f"Updating code_element_group {code_element_group.id}",
            update_schema=self._merge_update_fields,
        )

    async def delete(self, code_element_group_id: str):
        query = WQ().woql_and(
            WQ().opt(
                WQ().woql_and(
                    # Find parent (if exists)
                    WQ().triple("v:parent", "code_element_group", code_element_group_id),

                    # Bind current node
                    WQ().eq("v:current", code_element_group_id),

                    WQ().opt(
                        WQ().triple("v:current", "class_children", "v:child").
                        delete_triple("v:current", "class_children", "v:child").
                        add_triple("v:parent", "class_children", "v:child")

                    ),
                    WQ().opt(
                        WQ().triple("v:current", "function_children", "v:func_child").
                        delete_triple("v:current", "function_children", "v:func_child").
                        add_triple(
                            "v:parent", "function_children", "v:func_child")
                    ),
                    WQ().opt(
                        WQ().triple("v:current", "code_element_group_children", "v:child").
                        delete_triple("v:current", "code_element_group_children", "v:child").
                        add_triple(
                            "v:parent", "code_element_group_children", "v:child")
                    ),


                    WQ().delete_triple(
                        "v:parent", "code_element_group_children", code_element_group_id)
                )
            ),
            WQ().delete_document(code_element_group_id),
        )
        try:
            await self.client.query(query, commit_msg=f"Deleting code_element_group {code_element_group_id}")
        except Exception as exc:
            print(exc)
            return False
        return True

    async def create_and_move_items(
        self,
        code_element_group: CodeElementGroupNode,
        items: List[Tuple[str, str]],
        parent_id: Optional[str] = None,
    ) -> bool:
        """Create group and move items in a single transaction. If any step fails, none are applied."""
        queries = []

        schema = CodeElementGroupSchema.from_pydantic(
            code_element_group)._obj_to_dict()[0]
        queries.append(WQ().insert_document(Doc(schema)))

        if parent_id:
            queries.append(
                WQ().add_triple(parent_id, "code_element_group", code_element_group.id)
            )

        for item in items:
            item_field = CODE_CHILD_TYPE_TO_FIELD.get(item[1])
            if not item_field:
                raise ValueError(f"Invalid code element child type: {item[1]}")
            queries.append(WQ().woql_and(
                WQ().opt(
                    WQ().triple("v:parent", item_field, item[0])
                    .delete_triple("v:parent", item_field, item[0])
                ),
                WQ().add_triple(code_element_group.id, item_field, item[0])
            ))

        combined = WQ().woql_and(*queries)

        try:
            await self.client.query(
                combined,
                commit_msg=f"Creating and moving items to code_element group {code_element_group.id}",
            )
        except Exception as exc:
            print(exc)
            return False
        return True
