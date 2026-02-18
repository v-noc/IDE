from typing import Dict, List, Tuple, Union

from app.core.model.nodes import FileNode
from app.core.model.schemas import CallGroupSchema, CallSchema, ClassSchema, CodeElementGroupSchema, FileSchema, FunctionSchema
from app.core.repository.base_repo import BaseRepo
from app.core.repository.utils import (
    CODE_CHILD_TYPE_TO_FIELD,
    CODE_ELEMENT_FIELDS,
    CODE_OPTIONAL_FIELDS_TO_PRESERVE,
    CODE_SET_FIELDS_TO_PRESERVE,
    build_path_field_name,
    parse_code_element_child,
)
from app.db.async_terminus_client import WOQLQuery as WQ
from app.db.async_terminus_client import AsyncClient


class FileRepo(BaseRepo[FileNode, FileSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, FileNode, FileSchema)

    @staticmethod
    def _merge_update_fields(
        existing_raw: dict,
        _file: FileNode,
        file_schema: FileSchema,
    ):
        BaseRepo.merge_set_fields(
            file_schema, existing_raw, CODE_SET_FIELDS_TO_PRESERVE)
        BaseRepo.merge_fields(file_schema, existing_raw,
                              CODE_OPTIONAL_FIELDS_TO_PRESERVE)

    async def create(
        self,
        file: Union[FileNode, List[FileNode]],
        project_db_name: str,
    ):
        return await self.create_nodes(
            file,
            project_db_name,
            singular_name="file",
            plural_name="files",
        )

    async def get_children(
        self,
        file_id: str,
        exclude_types: list[str],
        project_db_name: str,
    ):

        field_name = build_path_field_name([], CODE_ELEMENT_FIELDS)
        field_to_schema_type = {
            FunctionSchema.__name__,
            ClassSchema.__name__,
            CallSchema.__name__,
            CodeElementGroupSchema.__name__,
            CallGroupSchema.__name__,
        }
        filtered_types = set(field_to_schema_type) - set(exclude_types)
        return await self.get_children_by_path(
            file_id,
            field_name,
            parse_code_element_child,
            project_db_name,
            filtered_types=filtered_types,
            allowed_path_fields=CODE_ELEMENT_FIELDS,
        )

    async def delete(self, file_id: str, project_db_name: str):
        return await self.delete_with_parent_cleanup(
            file_id,
            parent_field="file_children",
            project_db_name=project_db_name,
            commit_msg=f"Deleting file {file_id}",
        )

    async def delete_batch(self, file_ids: List[str], project_db_name: str):
        return await self.delete_batch_with_parent_cleanup(
            file_ids,
            parent_field="file_children",
            binding_var="v:file_id",
            project_db_name=project_db_name,
            commit_msg=f"Deleting files {', '.join(file_ids[:5])}",
        )

    async def update(self, file: FileNode, project_db_name: str):
        return await self.update_node(
            file,
            project_db_name=project_db_name,
            commit_msg=f"Updating file {file.id}",
            update_schema=self._merge_update_fields,
        )

    async def update_batch(self, files: List[FileNode], project_db_name: str):
        return await self.update_nodes(
            files,
            project_db_name=project_db_name,
            commit_msg=f"Updating files {len(files)}",
            update_schema=self._merge_update_fields,
        )

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
            child_type_to_field=CODE_CHILD_TYPE_TO_FIELD,
            project_db_name=project_db_name,
        )

    async def move_batch(
        self,
        moves: List[Tuple[str, str, str]],
        project_db_name: str,
    ):
        return await self.move_batch_by_type(
            moves,
            child_type_to_field=CODE_CHILD_TYPE_TO_FIELD,
            project_db_name=project_db_name,
        )

    async def get_all_files(self, project_db_name: str):
        return await self.get_all(project_db_name)

    async def get_by_path(self, path: str, project_db_name: str):
        return await self.find("path", [path], project_db_name)

    async def get_by_qnames(
        self, qnames: List[str], project_db_name: str
    ) -> Dict[str, FileNode]:
        """Return a dict mapping qname -> FileNode for the given qnames."""
        nodes = await super().get_by_qnames(qnames, project_db_name)
        return {n.qname: n for n in nodes}

    async def get_parent_file(self, item_id: str, project_db_name: str):
        field_name = build_path_field_name(
            [], CODE_ELEMENT_FIELDS, is_inverse=True)

        query = WQ().select("v:parent_doc").woql_and(
            WQ().eq("v:item", item_id),
            WQ().path("v:item", f"{field_name}*", "v:parent"),
            WQ().isa("v:parent", f"@schema:{FileSchema.__name__}"),
            WQ().read_document("v:parent", "v:parent_doc"),
        )

        async with self.session(project_db_name):
            try:
                result = await self.client.query(query)
            except Exception as exc:
                print(exc)
                return None

        if not result["bindings"]:
            return None
        return FileNode.from_raw_dict(result["bindings"][0]["parent_doc"])
