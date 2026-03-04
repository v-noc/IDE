from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Union

from terminusdb_client.woqlquery.woql_query import Doc

from app.core.model.nodes import FileNode, FolderNode
from app.core.model.schemas import FileSchema, FolderSchema, StructureGroupSchema
from app.core.repository.base_repo import BaseRepo
from app.core.repository.utils import (
    CODE_SET_FIELDS_TO_PRESERVE,
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
    def _merge_folder_update_fields(
        existing_raw: dict,
        _folder: FolderNode,
        folder_schema: FolderSchema,
    ):
        BaseRepo.merge_set_fields(
            folder_schema, existing_raw, STRUCTURE_SET_FIELDS_TO_PRESERVE
        )

    @staticmethod
    def _merge_file_update_fields(
        existing_raw: dict,
        _file: FileNode,
        file_schema: FileSchema,
    ):
        BaseRepo.merge_set_fields(
            file_schema, existing_raw, CODE_SET_FIELDS_TO_PRESERVE
        )

    async def create(
        self,
        new_folder: Union[FolderNode, List[FolderNode]],
        raw: bool = False,
    ):
        return await self.create_nodes(
            new_folder,
            singular_name="folder",
            plural_name="folders",
            raw=raw,
        )

    async def delete(self, folder_id: str):
        return await self.delete_with_parent_cleanup(
            folder_id,
            parent_field="folder_children",
            commit_msg=f"Deleting folder {folder_id}",
        )

    async def delete_batch(self, folder_ids: List[str]):
        return await self.delete_batch_with_parent_cleanup(
            folder_ids,
            parent_field="folder_children",
            binding_var="v:folder_id",
            commit_msg=f"Deleting folders {', '.join(folder_ids)}",
        )

    async def update(self, folder: FolderNode):
        return await self.update_node(
            folder,
            commit_msg=f"Updating folder {folder.id}",
            update_schema=self._merge_folder_update_fields,
        )

    async def update_batch(
        self,
        nodes: List[Union[FolderNode, FileNode]],
    ):
        """
        Update both folders and files in a single request.
        Preserves set fields (children, documents) from existing documents.
        """
        if not nodes:
            return True

        item_ids = [n.id for n in nodes]
        try:
            items_raw = await self.client.get_documents(item_ids)
        except Exception as exc:
            print(exc)
            return False

        id_to_raw: Dict[str, dict] = {raw["@id"]: raw for raw in items_raw}
        if len(id_to_raw) != len(nodes):
            missing = set(item_ids) - set(id_to_raw.keys())
            print(f"Error: documents not found for update: {missing}")
            return False

        schemas: List[Union[FolderSchema, FileSchema]] = []
        for node in nodes:
            existing_raw = id_to_raw.get(node.id)
            if not existing_raw:
                continue
            if isinstance(node, FolderNode):
                schema = FolderSchema.from_pydantic(node)
                self._merge_folder_update_fields(existing_raw, node, schema)
            else:
                schema = FileSchema.from_pydantic(node)
                self._merge_file_update_fields(existing_raw, node, schema)
            schema.updated_at = datetime.now(timezone.utc)
            schemas.append(schema)

        try:
            await self.client.update_document(
                schemas,
                commit_msg=f"Updating structure: {len(schemas)} items (folders + files)",
            )
        except Exception as exc:
            print(exc)
            return False
        return True

    async def get_children(
        self,
        folder_id: str,
        exclude_types: list[str],
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
            filtered_types=list(filtered_types),
            allowed_path_fields=STRUCTURE_FIELDS,
        )

    async def get_parent(
        self,
        item_id: str,
        child_type: str,
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
    ):
        return await self.move_item_by_type(
            new_parent_id,
            item_id,
            child_type,
            child_type_to_field=STRUCTURE_CHILD_TYPE_TO_FIELD,
        )

    async def move_batch(
        self,
        moves: List[Tuple[str, str, str]],
    ):
        return await self.move_batch_by_type(
            moves,
            child_type_to_field=STRUCTURE_CHILD_TYPE_TO_FIELD,
        )

    async def get_all_folders(self):
        return await self.get_all()

    async def get_by_qnames(self, qnames: List[str]) -> Dict[str, FolderNode]:
        """Return a dict mapping qname -> FolderNode for the given qnames."""
        nodes = await super().get_by_qnames(qnames)
        return {n.qname: n for n in nodes}

    async def flush_batch(self, insert: List[FolderNode | FileNode], update: List[FolderNode | FileNode], delete: List[str], move: List[Tuple[str, str, str]]):
        if not insert and not update and not delete and not move:
            return True

        queries = []

        # build delete operations
        for delete_id in delete:
            queries.append(WQ().delete_document(delete_id))

        # build insert operations
        for node in insert:
            if isinstance(node, FolderNode):
                schema = FolderSchema.from_pydantic(node)._obj_to_dict()[0]
            elif isinstance(node, FileNode):
                schema = FileSchema.from_pydantic(node)._obj_to_dict()[0]
            else:
                raise ValueError(f"Invalid node type: {type(node)}")
            queries.append(WQ().insert_document(Doc(schema)))

        for node in update:
            queries.append(WQ().woql_and(
                WQ().update_triple(node.id, "qname", WQ().string(node.qname)),
                WQ().update_triple(node.id, "path", WQ().string(node.path)),

            ))

        for item_id, new_parent_id, child_type in move:
            field = STRUCTURE_CHILD_TYPE_TO_FIELD.get(child_type)
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
