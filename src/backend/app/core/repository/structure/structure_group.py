from app.core.repository.base_repo import WQ, BaseRepo
from app.db.async_terminus_client import AsyncClient
from app.core.model.nodes import StructureGroupNode
from app.core.model.schemas import StructureGroupSchema
from app.core.repository.structure.folder_repo import STRUCTURE_CHILD_TYPE_TO_FIELD, STRUCTURE_SET_FIELDS_TO_PRESERVE
from typing import List, Optional, Tuple
from typing import Literal


class StructureGroupRepo(BaseRepo[StructureGroupNode, StructureGroupSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, StructureGroupNode, StructureGroupSchema)

    @staticmethod
    def _merge_update_fields(existing_raw: dict, _node: StructureGroupNode, schema: StructureGroupSchema):
        BaseRepo.merge_set_fields(
            schema, existing_raw, STRUCTURE_SET_FIELDS_TO_PRESERVE)

    async def create(self, structure_group: StructureGroupNode, project_db_name: str, branch_name: Optional[str] = None):
        return await self.create_nodes(
            structure_group,
            project_db_name,
            singular_name="structure_group",
            plural_name="structure_groups",
            branch_name=branch_name,
        )

    async def move_item(self,
                        new_parent_id: str,
                        item_id: str,
                        child_type: str,
                        project_db_name: str,
                        branch_name: Optional[str] = None):
        return await self.move_item_by_type(
            new_parent_id,
            item_id,
            child_type,
            child_type_to_field=STRUCTURE_CHILD_TYPE_TO_FIELD,
            project_db_name=project_db_name,
            branch_name=branch_name,
        )

    async def move_batch(self, moves: List[Tuple[str, str, str]], project_db_name: str, branch_name: Optional[str] = None):
        return await self.move_batch_by_type(
            moves,
            child_type_to_field=STRUCTURE_CHILD_TYPE_TO_FIELD,
            project_db_name=project_db_name,
            branch_name=branch_name,
        )

    async def delete(
            self,
            structure_group_id: str,
            project_db_name: str,
            branch_name: Optional[str] = None):
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
        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                await new_client.query(query, commit_msg=f"Deleting structure_group {structure_group_id}")

            except Exception as exc:
                print(exc)
                return False
        return True
