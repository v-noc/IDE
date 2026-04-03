from typing import AbstractSet, Any, List, Literal, Optional, Tuple, Union

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

    async def get_call_chain(self, call_id: str):
        query = WQ().select("v:parent_doc", "v:owner").woql_and(
            WQ().eq("v:call", call_id).
            path("v:call", "(<call_children|<call_group>)*", "v:owner")
            .read_document("v:owner", "v:parent_doc")
        )
        try:
            result = await self.client.query(query)
            if len(result["bindings"]) == 0:
                return None
            return [parse_structure_child(row["parent_doc"]) for row in result["bindings"]]
        except Exception as exc:
            print(exc)
            return []

    async def create(
        self,
        call: Union[CallNode, List[CallNode]],
    ):
        return await self.create_nodes(
            call,
            singular_name="call",
            plural_name="calls",
        )

    async def get_by_id(self, call_id: str, raw: bool = False):
        return await super().get_by_id(call_id, raw)

    async def delete(self, call_id: str):
        return await self.delete_with_parent_cleanup(
            call_id,
            parent_field="call_children",
            commit_msg=f"Deleting call {call_id}",
        )

    async def batch_delete_calls(self, call_ids: List[str]):
        return await self.delete_batch_with_parent_cleanup(
            call_ids, "call_children", "v:call_id", f"Deleting calls {call_ids}"
        )

    async def update(self, call: CallNode):
        return await self.update_node(
            call,
            commit_msg=f"Updating call {call.name}",
            update_schema=self._merge_update_fields,
        )

    async def move_item(
        self,
        new_parent_id: str,
        item_id: str,
        item_type: Literal["call", "call_group"],
    ):
        return await self.move_item_by_type(
            new_parent_id,
            item_id,
            item_type,
            child_type_to_field=CALL_CHILD_TYPE_TO_FIELD,
        )

    async def move_batch(self, moves: List[Tuple[str, str, str]]):
        return await self.move_batch_by_type(
            moves,
            child_type_to_field=CALL_CHILD_TYPE_TO_FIELD,
        )

    async def get_children(
        self,
        call_site_id: str,
        child_type: list[Literal["call", "call_group"]],
    ):
        field_name = build_path_field_name(
            child_type, list(CALL_FIELDS)
        )
        return await self.get_children_by_path(
            call_site_id,
            field_name,
            parse_code_element_child,
            allowed_path_fields=CALL_FIELDS,
        )

    def _woql_delete_calls_with_parent_cleanup(self, call_ids: List[str]) -> List[Any]:
        queries = []
        for call_id in call_ids:
            queries.append(
                WQ().woql_and(
                    WQ().opt(
                        WQ()
                        .triple("v:parent", "call_children", call_id)
                        .delete_triple("v:parent", "call_children", call_id)
                    ),
                    WQ().delete_document(call_id),
                )
            )
        return queries

    def _woql_moves(
        self,
        moves: List[Tuple[str, str, str]],
        insert_ids: AbstractSet[str],
    ) -> List[Any]:
        queries = []
        for item_id, new_parent_id, child_type in moves:
            field = CALL_CHILD_TYPE_TO_FIELD.get(child_type, "call_children")
            if item_id in insert_ids:
                queries.append(WQ().add_triple(new_parent_id, field, item_id))
            else:
                queries.append(
                    WQ().woql_and(
                        WQ().opt(
                            WQ()
                            .triple("v:old_parent", field, item_id)
                            .delete_triple("v:old_parent", field, item_id)
                        ),
                        WQ().add_triple(new_parent_id, field, item_id),
                    )
                )
        return queries

    async def flush_delete_move_batch_chunked(
        self,
        deletes: List[str],
        moves: List[Tuple[str, str, str]],
        *,
        insert_ids: Optional[AbstractSet[str]] = None,
        chunk_size: int = 5000,
    ) -> bool:
        """
        Delete and move operations in combined WOQL per chunk (up to chunk_size deletes
        and chunk_size moves each round). Inserts are handled separately via create().
        """
        if not deletes and not moves:
            return True

        known_new_ids: AbstractSet[str] = insert_ids if insert_ids is not None else frozenset()
        di, mi = 0, 0
        while di < len(deletes) or mi < len(moves):
            d_chunk = deletes[di : di + chunk_size]
            di += len(d_chunk)
            m_chunk = moves[mi : mi + chunk_size]
            mi += len(m_chunk)
            if not d_chunk and not m_chunk:
                break
            parts = self._woql_delete_calls_with_parent_cleanup(
                d_chunk
            ) + self._woql_moves(m_chunk, known_new_ids)
            if not parts:
                continue
            combined = WQ().woql_and(*parts)
            try:
                await self.client.query(
                    combined,
                    commit_msg=(
                        f"Batch delete+move: {len(d_chunk)} deletes, {len(m_chunk)} moves"
                    ),
                )
            except Exception as exc:
                print(f"Batch delete+move chunk failed: {exc}")
                return False
        return True

    async def get_direct_children(self, call_site_id: str, child_type: str):
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
        try:
            result = await self.client.query(query)
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
