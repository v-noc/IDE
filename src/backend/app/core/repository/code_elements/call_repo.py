from typing import List, Literal, Optional, Tuple, Union

from terminusdb_client.woqlquery.woql_query import Doc
from app.db.async_terminus_client import WOQLQuery as WQ
from app.core.model.nodes import CallNode
from app.core.model.schemas.code_element_schema import CallSchema
from app.core.repository.base_repo import BaseRepo
from app.core.repository.utils import (
    CALL_FIELDS,
    CODE_CHILD_TYPE_TO_FIELD,
    CALL_CHILD_TYPE_TO_FIELD,
    CALL_SET_FIELDS_TO_PRESERVE,
    CALL_OPTIONAL_FIELDS_TO_PRESERVE,
    build_path_field_name,
    parse_code_element_child,
    parse_structure_child,
)
from app.db.async_terminus_client import AsyncClient
from app.core.model.schemas import FunctionSchema, ClassSchema
from app.core.model.schemas import FileSchema

# Call-specific fields to preserve on update (CallSchema only has call_children, call_group, documents)


class CallRepo(BaseRepo[CallNode, CallSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, CallNode, CallSchema)

    @staticmethod
    def _merge_update_fields(
        existing_raw: dict,
        _call: CallNode,
        call_schema: CallSchema,
    ):
        BaseRepo.merge_set_fields(
            call_schema, existing_raw, CALL_SET_FIELDS_TO_PRESERVE
        )
        BaseRepo.merge_fields(
            call_schema, existing_raw, CALL_OPTIONAL_FIELDS_TO_PRESERVE
        )

    async def get_call_chain(self, call_id: str, project_db_name: str, branch_name: Optional[str] = None):
        query = WQ().select("v:parent_doc", "v:owner").woql_and(
            WQ().eq("v:call", call_id).
            path("v:call", "(<call_children|<call_group>)*", "v:owner")
            .read_document("v:owner", "v:parent_doc")
        )
        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                result = await new_client.query(query)
                if len(result["bindings"]) == 0:
                    return None

                return [parse_structure_child(row["parent_doc"]) for row in result["bindings"]]
            except Exception as exc:
                print(exc)
                return []

    async def create(
        self,
        call: Union[CallNode, List[CallNode]],
        project_db_name: str,
        branch_name: Optional[str] = None,
    ):
        return await self.create_nodes(
            call,
            project_db_name,
            singular_name="call",
            plural_name="calls",
            branch_name=branch_name,
        )

    async def get_by_id(self, call_id: str, project_db_name: str, raw: bool = False, branch_name: Optional[str] = None):
        return await super().get_by_id(call_id, project_db_name, raw=raw, branch_name=branch_name)

    async def delete(self, call_id: str, project_db_name: str, branch_name: Optional[str] = None):
        return await self.delete_with_parent_cleanup(
            call_id,
            parent_field="call_children",
            project_db_name=project_db_name,
            commit_msg=f"Deleting call {call_id}",
            branch_name=branch_name,
        )

    async def batch_delete_calls(self, call_ids: List[str], project_db_name: str):
        return await self.delete_batch_with_parent_cleanup(call_ids, "call_children", "v:call_id", project_db_name, f"Deleting calls {call_ids}")

    async def update(self, call: CallNode, project_db_name: str):
        return await self.update_node(
            call,
            project_db_name=project_db_name,
            commit_msg=f"Updating call {call.name}",
            update_schema=self._merge_update_fields,
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
            child_type_to_field=CALL_CHILD_TYPE_TO_FIELD,
            project_db_name=project_db_name,
            branch_name=branch_name,
        )

    async def get_children(
        self,
        call_site_id: str,
        child_type: list[Literal["call", "call_group"]],
        project_db_name: str,
        branch_name: Optional[str] = None,
    ):
        field_name = build_path_field_name(
            child_type, list(CALL_FIELDS)
        )
        return await self.get_children_by_path(
            call_site_id,
            field_name,
            parse_code_element_child,
            project_db_name,
            allowed_path_fields=CALL_FIELDS,
            branch_name=branch_name,
        )

    async def _flush_batch_combined(self, inserts: List[CallNode], deletes: List[str], moves: List[Tuple[str, str, str]], project_db_name: str, branch_name: Optional[str] = None):
        """Execute inserts, deletes, and moves in one atomic WOQL query."""
        if not inserts and not deletes and not moves:
            return True

        queries = []
        for call_node in inserts:

            # # or .dict() depending on your Pydantic version
            call_dict = CallSchema.from_pydantic(
                call_node)._obj_to_dict()[0]

            queries.append(WQ().insert_document(Doc(call_dict)))

        # Build delete operations (with parent cleanup)
        for call_id in deletes:
            queries.append(
                WQ().woql_and(
                    WQ().opt(
                        WQ().triple("v:parent", "call_children", call_id)
                        .delete_triple("v:parent", "call_children", call_id)
                    ),
                    WQ().delete_document(call_id)
                )
            )

        # Build move operations (remove from old parent, add to new)
        for item_id, new_parent_id, child_type in moves:
            field = CALL_CHILD_TYPE_TO_FIELD.get(child_type, "call_children")
            is_new_item = False
            for node in inserts:
                if node.id == item_id:
                    is_new_item = True
                    break
            if is_new_item:
                queries.append(WQ().add_triple(new_parent_id, field, item_id))
            else:
                queries.append(
                    WQ().woql_and(
                        WQ().opt(
                            WQ().triple("v:old_parent", field, item_id)
                            .delete_triple("v:old_parent", field, item_id)
                        ),
                        WQ().add_triple(new_parent_id, field, item_id)
                    )
                )

        # Build insert operations
        # Note: Convert Pydantic models to dicts compatible with WOQL

        if not queries:
            return True

        combined = WQ().woql_and(*queries)

        async with self.session(project_db_name, branch_name=branch_name) as client:
            try:
                await client.query(combined, commit_msg=f"Batch: {len(inserts)} inserts, {len(deletes)} deletes, {len(moves)} moves")
                return True
            except Exception as exc:
                print(f"Batch operation failed: {exc}")
                return False

    async def get_direct_children(self, call_site_id: str, child_type: str, project_db_name: str, branch_name: Optional[str] = None):
        query = WQ().select("v:child_doc", "v:target_doc").woql_and(
            WQ().eq("v:call_site", call_site_id).
            path("v:call_site", "call_children|call_group", "v:child").
            triple("v:child",
                   "rdf:type", "v:type")
            .triple("v:child", "target_function", "v:target")
            .member("v:type", [f"@schema:{child_type}"])
            .read_document("v:target", "v:target_doc")
            .read_document("v:child", "v:child_doc")
        )
        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                result = await new_client.query(query)
                bindings = result["bindings"]
                children = []
                for binding in bindings:
                    child = binding["child_doc"]
                    target = binding["target_doc"]
                    children.append(
                        {"call": parse_code_element_child(child), "target": parse_code_element_child(target)})
                return children
            except Exception as exc:
                print(exc)
                return []
