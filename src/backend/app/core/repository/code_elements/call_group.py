from typing import Literal, Optional, List, Tuple
from terminusdb_client.woqlquery.woql_query import Doc
from app.core.repository.base_repo import BaseRepo, WQ
from app.db.async_terminus_client import AsyncClient
from app.core.model.nodes import CallGroupNode
from app.core.model.schemas import CallGroupSchema
from app.core.repository.utils import CALL_FIELDS, CALL_CHILD_TYPE_TO_FIELD, CALL_SET_FIELDS_TO_PRESERVE, build_path_field_name, parse_call_child


class CallGroupRepo(BaseRepo[CallGroupNode, CallGroupSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, CallGroupNode, CallGroupSchema)

    @staticmethod
    def _merge_update_fields(existing_raw: dict, _node: CallGroupNode, schema: CallGroupSchema):
        BaseRepo.merge_set_fields(
            schema, existing_raw, CALL_SET_FIELDS_TO_PRESERVE)

    async def create(self, call_group: CallGroupNode, project_db_name: str, branch_name: Optional[str] = None):
        return await self.create_nodes(
            call_group,
            project_db_name,
            singular_name="call_group",
            plural_name="call_groups",
            branch_name=branch_name,
        )

    async def move_item(
        self,
        new_parent_id: str,
        item_id: str,
        item_type: Literal["call", "call_group"],
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

    async def get_children(self, call_group_id: str, project_db_name: str, branch_name: Optional[str] = None):
        field_name = build_path_field_name(
            [], list(CALL_FIELDS)
        )
        return await self.get_children_by_path(
            call_group_id,
            field_name,
            parse_call_child,
            project_db_name,
            allowed_path_fields=CALL_FIELDS,
            branch_name=branch_name,
        )

    async def update(self, call_group: CallGroupNode, project_db_name: str, branch_name: Optional[str] = None):
        return await self.update_node(
            call_group,
            project_db_name,
            commit_msg=f"Updating call_group {call_group.id}",
            update_schema=self._merge_update_fields,
            branch_name=branch_name,
        )

    async def delete(self, code_element_group_id: str, project_db_name: str, branch_name: Optional[str] = None):
        query = WQ().woql_and(
            WQ().opt(
                WQ().woql_and(
                    WQ().triple("v:parent", "call_group", code_element_group_id),
                    WQ().eq("v:current", code_element_group_id),


                    WQ().opt(
                        WQ().triple("v:current", "call_children", "v:child").
                        delete_triple("v:current", "call_children", "v:child").
                        add_triple(
                            "v:parent", "call_children", "v:child")
                    ),
                    WQ().opt(
                        WQ().triple("v:current", "call_group", "v:child").
                        delete_triple("v:current", "call_group", "v:child").
                        add_triple(
                            "v:parent", "call_group", "v:child")
                    ),


                    WQ().delete_triple(
                        "v:parent", "call_group", code_element_group_id)
                )
            ),
            WQ().delete_document(code_element_group_id),
        )
        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                await new_client.query(query, commit_msg=f"Deleting code_element_group {code_element_group_id}")
            except Exception as exc:
                print(exc)
                return False
        return True

    async def create_and_move_items(
        self,
        call_group: CallGroupNode,
        items: List[Tuple[str, str]],
        project_db_name: str,
        branch_name: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> bool:
        """Create group and move items in a single transaction. If any step fails, none are applied."""
        queries = []

        schema = CallGroupSchema.from_pydantic(
            call_group)._obj_to_dict()[0]
        queries.append(WQ().insert_document(Doc(schema)))

        if parent_id:
            queries.append(
                WQ().add_triple(parent_id, "call_group", call_group.id)
            )

        for item in items:
            item_field = CALL_CHILD_TYPE_TO_FIELD.get(item[1])
            if not item_field:
                raise ValueError(f"Invalid call child type: {item[1]}")
            queries.append(WQ().woql_and(
                WQ().opt(
                    WQ().triple("v:parent", item_field, item[0])
                    .delete_triple("v:parent", item_field, item[0])
                ),
                WQ().add_triple(call_group.id, item_field, item[0])
            ))

        combined = WQ().woql_and(*queries)

        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                await new_client.query(
                    combined,
                    commit_msg=f"Creating and moving items to call group {call_group.id}",
                )
            except Exception as exc:
                print(exc)
                return False
        return True
