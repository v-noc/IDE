from typing import Any, List, Tuple, Union
from app.core.model.nodes import FolderNode, FileNode, StructureGroupNode
from app.core.model.schemas import (
    CodeContentSchema,
    FolderSchema,
    FileSchema,
    StructureGroupSchema,
    FunctionSchema,
    ClassSchema,
    CallSchema,
    CodeElementGroupSchema,
    CallGroupSchema,
)
from app.core.model.schemas.structure_schema import _code_content_id_for_file
from app.core.repository.base_repo import BaseRepo
from app.db.async_terminus_client import AsyncClient

from terminusdb_client.woqlquery.woql_query import Doc, WOQLQuery as WQ
from app.core.repository.utils import (
    CODE_CHILD_TYPE_TO_FIELD,
    CODE_ELEMENT_FIELDS,
    CODE_SET_FIELDS_TO_PRESERVE,
    STRUCTURE_FIELDS,
    build_path_field_name,
    parse_structure_child,
)
STRUCTURE_SET_FIELDS_TO_PRESERVE = [
    "folder_children",
    "file_children",
    "structure_group",
    "documents",
]
STRUCTURE_CHILD_TYPE_TO_FIELD = {
    "folder": "folder_children",
    "file": "file_children",
    "structure_group": "structure_group",
}
StructureNode = Union[FolderNode, FileNode, StructureGroupNode]
StructureSchema = Union[FolderSchema, FileSchema, StructureGroupSchema]


class StructureRepo(BaseRepo[StructureNode, StructureSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, StructureNode, StructureSchema)

    @staticmethod
    def _merge_update_fields(existing_raw: dict, _node: StructureNode, schema: StructureSchema):
        if isinstance(_node, FolderNode):
            return StructureRepo._merge_folder_update_fields(existing_raw, _node, schema)
        elif isinstance(_node, FileNode):
            return StructureRepo._merge_file_update_fields(existing_raw, _node, schema)
        else:
            raise ValueError(f"Invalid node type: {type(_node)}")

    @staticmethod
    def _merge_folder_update_fields(existing_raw: dict, _node: FolderNode, schema: FolderSchema):
        BaseRepo.merge_set_fields(
            schema, existing_raw, STRUCTURE_SET_FIELDS_TO_PRESERVE)

    @staticmethod
    def _merge_file_update_fields(existing_raw: dict, _node: FileNode, schema: FileSchema):
        BaseRepo.merge_set_fields(
            schema, existing_raw, CODE_SET_FIELDS_TO_PRESERVE)
        # Preserve code_content link so file updates don't overwrite it
        schema.code_content = CodeContentSchema.from_file_content(_node.id, "")

    def _to_node(self, raw_data: dict[str, Any]) -> StructureNode:
        if raw_data["@type"] == "FolderSchema":
            return FolderNode.from_raw_dict(raw_data)
        elif raw_data["@type"] == "FileSchema":
            return FileNode.from_raw_dict(raw_data)
        elif raw_data["@type"] == "StructureGroupSchema":
            return StructureGroupNode.from_raw_dict(raw_data)
        else:
            raise ValueError(f"Invalid node type: {raw_data['@type']}")

    def _to_schema(self, node: StructureNode) -> StructureSchema:
        if isinstance(node, FolderNode):
            return FolderSchema.from_pydantic(node)
        elif isinstance(node, FileNode):
            return FileSchema.from_pydantic(node)
        elif isinstance(node, StructureGroupNode):
            return StructureGroupSchema.from_pydantic(node)
        else:
            raise ValueError(f"Invalid node type: {type(node)}")

    async def create(self, structure: StructureNode | List[StructureNode]):
        return await self.create_nodes(
            structure,
            singular_name="structure",
            plural_name="structures",
        )

    async def delete(self, structure_id: str):
        return await self.delete_with_parent_cleanup(
            structure_id,
            parent_field="structure_children",
            commit_msg=f"Deleting structure {structure_id}",
        )

    async def update(self, structure: StructureNode):
        return await self.update_node(
            structure,
            commit_msg=f"Updating structure {structure.id}",
            update_schema=self._merge_update_fields,
        )

    async def move_item(self, new_parent_id: str, item_id: str, child_type: str):
        STRUCTURE_CHILD_TYPE_TO_FIELD.update(CODE_CHILD_TYPE_TO_FIELD)
        return await self.move_item_by_type(
            new_parent_id,
            item_id,
            child_type,
            child_type_to_field=STRUCTURE_CHILD_TYPE_TO_FIELD,
        )

    async def move_batch(self, moves: List[Tuple[str, str, str]]):
        STRUCTURE_CHILD_TYPE_TO_FIELD.update(CODE_CHILD_TYPE_TO_FIELD)
        return await self.move_batch_by_type(moves, STRUCTURE_CHILD_TYPE_TO_FIELD)

    async def update_batch(self, structures: List[StructureNode]):
        if not structures:
            return True

        items_raw = await self.get_by_ids([n.id for n in structures], raw=True)
        id_to_raw = {r["@id"]: r for r in items_raw} if items_raw else {}

        schemas = []

        for node in structures:
            existing_raw = id_to_raw.get(node.id)
            if not existing_raw:
                continue

            # Determine correct schema class
            schema_cls = FolderSchema if isinstance(
                node, FolderNode) else FileSchema
            schema = schema_cls.from_pydantic(node)

            self._merge_update_fields(existing_raw, node, schema)
            self.touch_updated_at(schema)
            schemas.append(schema)

        if not schemas:
            return True
        return await self.client.update_document(schemas, commit_msg=f"Updating {len(schemas)} structures")

    async def get_children(self, parent_id: str,  exclude_types: list[str],):

        field_name = build_path_field_name(
            [], STRUCTURE_FIELDS+CODE_ELEMENT_FIELDS)
        field_to_schema_type = {
            FolderSchema.__name__,
            FileSchema.__name__,
            StructureGroupSchema.__name__,
            FunctionSchema.__name__,
            ClassSchema.__name__,
            CallSchema.__name__,
            CodeElementGroupSchema.__name__,
            CallGroupSchema.__name__,
        }
        filtered_types = set(field_to_schema_type) - set(exclude_types)

        return await self.get_children_by_path(
            parent_id,
            field_name,
            parse_structure_child,
            filtered_types=list(filtered_types),
            allowed_path_fields=STRUCTURE_FIELDS+CODE_ELEMENT_FIELDS,
        )

    async def get_parent_file(self, item_id: str):
        field_name = build_path_field_name(
            [], CODE_ELEMENT_FIELDS, is_inverse=True)

        query = WQ().select("v:parent_doc").woql_and(
            WQ().eq("v:item", item_id),
            WQ().path("v:item", f"{field_name}*", "v:parent"),
            WQ().isa("v:parent", f"@schema:{FileSchema.__name__}"),
            WQ().read_document("v:parent", "v:parent_doc"),
        )

        try:
            result = await self.client.query(query)
        except Exception as exc:
            print(exc)
            return None

        if not result["bindings"]:
            return None
        return FileNode.from_raw_dict(result["bindings"][0]["parent_doc"])

    async def get_by_qnames(self, qnames: list[str], doc_type: str | None = None) -> list[StructureNode]:
        nodes = await super().get_by_qnames(qnames, doc_type)
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
                queries.append(WQ().insert_document(Doc(schema)))
            elif isinstance(node, FileNode):

                file_schema = FileSchema.from_pydantic(node)

                content_id = _code_content_id_for_file(node.id)
                file_schema.code_content = content_id
                file_schema = file_schema._obj_to_dict()[0]
                # Insert empty CodeContent placeholder first so file commits track content
                content_schema = CodeContentSchema.from_file_content(
                    node.id, ""
                )._obj_to_dict()[0]
                queries.append(WQ().insert_document(Doc(content_schema)))
                queries.append(WQ().insert_document(Doc(file_schema)))
            else:
                raise ValueError(f"Invalid node type: {type(node)}")

        # for node in update:
        #     queries.append(WQ().woql_and(
        #         WQ().update_triple(node.id, "qname", WQ().string(node.qname)),
        #         WQ().update_triple(node.id, "path", WQ().string(node.path)),

        #     ))

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

    async def flush_content_batch(
        self,
        inserts: List[Tuple[str, str]],
        updates: List[Tuple[str, str]],
    ) -> bool:
        """
        Batch insert/update CodeContent documents.
        Each tuple is (file_id, content).
        Uses client.update_document which upserts (add if not existed).
        Single API call for all content ops.
        """
        all_ops = list(inserts) + list(updates)
        if not all_ops:
            return True

        schemas = [
            CodeContentSchema.from_file_content(file_id, content)
            for file_id, content in all_ops
        ]
        try:
            await self.client.update_document(
                schemas,
                commit_msg=f"Batch: {len(all_ops)} file content upserts",
            )
            return True
        except Exception as exc:
            print(f"Content batch operation failed: {exc}")
            return False
