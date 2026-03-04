from terminusdb_client.woqlquery.woql_query import Doc
from app.core.repository.base_repo import WQ, BaseRepo
from app.db.async_terminus_client import AsyncClient
from app.core.model.nodes import StructureGroupNode
from app.core.model.schemas import StructureGroupSchema
from app.core.repository.structure.folder_repo import STRUCTURE_CHILD_TYPE_TO_FIELD, STRUCTURE_SET_FIELDS_TO_PRESERVE
from typing import List, Optional, Tuple


class StructureGroupRepo(BaseRepo[StructureGroupNode, StructureGroupSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, StructureGroupNode, StructureGroupSchema)

    @staticmethod
    def _merge_update_fields(existing_raw: dict, _node: StructureGroupNode, schema: StructureGroupSchema):
        BaseRepo.merge_set_fields(
            schema, existing_raw, STRUCTURE_SET_FIELDS_TO_PRESERVE)

    async def create(self, structure_group: StructureGroupNode):
        return await self.create_nodes(
            structure_group,
            singular_name="structure_group",
            plural_name="structure_groups",
        )

    async def move_item(self, new_parent_id: str, item_id: str, child_type: str):
        return await self.move_item_by_type(
            new_parent_id,
            item_id,
            child_type,
            child_type_to_field=STRUCTURE_CHILD_TYPE_TO_FIELD,
        )

    async def move_batch(self, moves: List[Tuple[str, str, str]]):
        return await self.move_batch_by_type(
            moves,
            child_type_to_field=STRUCTURE_CHILD_TYPE_TO_FIELD,
        )

    async def update(self, structure_group: StructureGroupNode):
        return await self.update_node(
            structure_group,
            commit_msg=f"Updating structure_group {structure_group.id}",
            update_schema=self._merge_update_fields,
        )

    async def delete(self, structure_group_id: str):
        query = WQ().woql_and(
            WQ().opt(
                WQ().woql_and(
                    # Find parent (if exists)
                    WQ().triple("v:parent", "structure_group", structure_group_id),

                    # Bind current node
                    WQ().eq("v:current", structure_group_id),

                    WQ().opt(
                        WQ().triple("v:current", "folder_children", "v:folder_child").
                        delete_triple("v:current", "folder_children", "v:folder_child").
                        add_triple("v:parent", "folder_children",
                                   "v:folder_child")

                    ),
                    WQ().opt(
                        WQ().triple("v:current", "file_children", "v:file_child").
                        delete_triple("v:current", "file_children", "v:file_child").
                        add_triple(
                            "v:parent", "file_children", "v:file_child")
                    ),
                    WQ().opt(
                        WQ().triple("v:current", "structure_group", "v:structure_group_child").
                        delete_triple("v:current", "structure_group", "v:structure_group_child").
                        add_triple(
                            "v:parent", "structure_group", "v:structure_group_child")
                    ),


                    WQ().delete_triple(
                        "v:parent", "structure_group", structure_group_id)
                )
            ),
            WQ().delete_document(structure_group_id),
        )
        try:
            await self.client.query(query, commit_msg=f"Deleting structure_group {structure_group_id}")
        except Exception as exc:
            print(exc)
            return False
        return True

    async def create_and_move_items(
        self,
        structure_group: StructureGroupNode,
        items: List[Tuple[str, str]],
        parent_id: Optional[str] = None,
    ) -> bool:
        """Create group and move items in a single transaction. If any step fails, none are applied."""
        queries = []

        schema = StructureGroupSchema.from_pydantic(
            structure_group)._obj_to_dict()[0]
        queries.append(WQ().insert_document(Doc(schema)))

        if parent_id:
            queries.append(
                WQ().add_triple(parent_id, "structure_group", structure_group.id)
            )

        for item in items:
            item_field = STRUCTURE_CHILD_TYPE_TO_FIELD.get(item[1])
            if not item_field:
                raise ValueError(f"Invalid structure child type: {item[1]}")
            queries.append(WQ().woql_and(
                WQ().opt(
                    WQ().triple("v:parent", item_field, item[0])
                    .delete_triple("v:parent", item_field, item[0])
                ),
                WQ().add_triple(structure_group.id, item_field, item[0])
            ))

        combined = WQ().woql_and(*queries)

        try:
            await self.client.query(
                combined,
                commit_msg=f"Creating and moving items to structure group {structure_group.id}",
            )
        except Exception as exc:
            print(exc)
            return False
        return True
