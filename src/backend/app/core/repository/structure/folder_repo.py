from typing import Dict, List, Tuple, Union

from app.core.model.nodes import FolderNode
from app.core.model.schemas import FileSchema, FolderSchema, StructureGroupSchema
from app.core.repository.base_repo import BaseRepo
from app.core.repository.utils import (
    STRUCTURE_FIELDS,
    build_path_field_name,
    parse_structure_child,
)
from app.db.async_terminus_client import AsyncClient
from app.db.async_terminus_client import WOQLQuery as WQ

STRUCTURE_CHILD_TYPE_TO_FIELD = {
    "folder": "folder_children",
    "file": "file_children",
    "structure_group": "structure_group",
}

STRUCTURE_SET_FIELDS_TO_PRESERVE = [
    "folder_children",
    "file_children",
    "structure_group",
    "documents",
]
STRUCTURE_OPTIONAL_FIELDS_TO_PRESERVE = ["theme_config"]


class FolderRepo(BaseRepo[FolderNode, FolderSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, FolderNode, FolderSchema)

    @staticmethod
    def _merge_update_fields(
        existing_raw: dict,
        _folder: FolderNode,
        folder_schema: FolderSchema,
    ):
        BaseRepo.merge_set_fields(
            folder_schema, existing_raw, STRUCTURE_SET_FIELDS_TO_PRESERVE
        )

    async def create(
        self,
        new_folder: Union[FolderNode, List[FolderNode]],
        project_db_name: str,
        raw: bool = False,
    ):
        return await self.create_nodes(
            new_folder,
            project_db_name,
            singular_name="folder",
            plural_name="folders",
            raw=raw,
        )

    async def delete(self, folder_id: str, project_db_name: str):
        return await self.delete_with_parent_cleanup(
            folder_id,
            parent_field="folder_children",
            project_db_name=project_db_name,
            commit_msg=f"Deleting folder {folder_id}",
        )

    async def delete_batch(self, folder_ids: List[str], project_db_name: str):
        return await self.delete_batch_with_parent_cleanup(
            folder_ids,
            parent_field="folder_children",
            binding_var="v:folder_id",
            project_db_name=project_db_name,
            commit_msg=f"Deleting folders {', '.join(folder_ids)}",
        )

    async def update(self, folder: FolderNode, project_db_name: str):
        return await self.update_node(
            folder,
            project_db_name=project_db_name,
            commit_msg=f"Updating folder {folder.id}",
            update_schema=self._merge_update_fields,
        )

    async def update_batch(
        self,
        folders: List[FolderNode],
        project_db_name: str,
    ):
        return await self.update_nodes(
            folders,
            project_db_name=project_db_name,
            commit_msg=f"Updating folders {len(folders)}",
            update_schema=self._merge_update_fields,
        )

    async def get_children(
        self,
        folder_id: str,
        exclude_types: list[str],
        project_db_name: str,
    ):
        field_name = build_path_field_name([], STRUCTURE_FIELDS)
        field_to_schema_type = {
            FolderSchema.__name__,
            FileSchema.__name__,
            StructureGroupSchema.__name__,
        }
        filtered_types = set(field_to_schema_type) - set(exclude_types)

        return await self.get_children_by_path(
            folder_id,
            field_name,
            parse_structure_child,
            project_db_name,
            filtered_types=filtered_types,
            allowed_path_fields=STRUCTURE_FIELDS,
        )

    async def get_parent(
        self,
        item_id: str,
        child_type: str,
        project_db_name: str,
    ):
        field_name = STRUCTURE_CHILD_TYPE_TO_FIELD.get(child_type)
        if not field_name:
            return None

        query = (
            WQ()
            .select("v:parent_doc")
            .woql_and(
                WQ()
                .triple("v:parent", field_name, "v:item")
                .eq("v:item", item_id)
                .read_document("v:parent", "v:parent_doc")
            )
        )
        async with self.session(project_db_name):
            try:
                result = await self.client.query(query)
            except Exception as exc:
                print(exc)
                return None
        return [row["parent_doc"] for row in result["bindings"]]

    async def move_item(
        self,
        new_parent_id: str,
        item_id: str,
        child_type: str,
        project_db_name: str,
    ):
        return await self.move_item_by_type(
            new_parent_id,
            item_id,
            child_type,
            child_type_to_field=STRUCTURE_CHILD_TYPE_TO_FIELD,
            project_db_name=project_db_name,
        )

    async def move_batch(
        self,
        moves: List[Tuple[str, str, str]],
        project_db_name: str,
    ):
        return await self.move_batch_by_type(
            moves,
            child_type_to_field=STRUCTURE_CHILD_TYPE_TO_FIELD,
            project_db_name=project_db_name,
        )

    async def get_all_folders(self, project_db_name: str):
        return await self.get_all(project_db_name)

    async def get_by_qnames(
        self, qnames: List[str], project_db_name: str
    ) -> Dict[str, FolderNode]:
        """Return a dict mapping qname -> FolderNode for the given qnames."""
        nodes = await super().get_by_qnames(qnames, project_db_name)
        return {n.qname: n for n in nodes}
