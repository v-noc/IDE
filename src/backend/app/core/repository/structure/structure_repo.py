from typing import Any, List, Tuple, Union
from app.core.model.nodes import FolderNode, FileNode, StructureGroupNode
from app.core.model.schemas import FolderSchema, FileSchema, StructureGroupSchema
from app.core.repository.base_repo import BaseRepo
from app.db.async_terminus_client import AsyncClient
from app.core.repository.utils import CODE_SET_FIELDS_TO_PRESERVE, CODE_CHILD_TYPE_TO_FIELD
from app.core.repository.structure.folder_repo import STRUCTURE_CHILD_TYPE_TO_FIELD
from terminusdb_client.woqlquery.woql_query import Doc, WOQLQuery as WQ

STRUCTURE_SET_FIELDS_TO_PRESERVE = [
    "folder_children",
    "file_children",
    "structure_group",
    "documents",
]

StructureNode = Union[FolderNode, FileNode, StructureGroupNode]
StructureSchema = Union[FolderSchema, FileSchema, StructureGroupSchema]


class StructureRepo(BaseRepo[StructureNode, StructureSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, StructureNode, StructureSchema)

    @staticmethod
    def _merge_folder_update_fields(existing_raw: dict, _node: FolderNode, schema: FolderSchema):
        BaseRepo.merge_set_fields(
            schema, existing_raw, STRUCTURE_SET_FIELDS_TO_PRESERVE)

    @staticmethod
    def _merge_file_update_fields(existing_raw: dict, _node: FileNode, schema: FileSchema):
        BaseRepo.merge_set_fields(
            schema, existing_raw, CODE_SET_FIELDS_TO_PRESERVE)

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

    async def create(self, structure: StructureNode):
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
        return await self.move_item_by_type(
            new_parent_id,
            item_id,
            child_type,
            child_type_to_field={
                *STRUCTURE_CHILD_TYPE_TO_FIELD, *CODE_CHILD_TYPE_TO_FIELD},
        )

    async def move_batch(self, moves: List[Tuple[str, str, str]]):
        return await self.move_batch_by_type(
            moves,
            child_type_to_field={
                *STRUCTURE_CHILD_TYPE_TO_FIELD, *CODE_CHILD_TYPE_TO_FIELD},
        )

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
