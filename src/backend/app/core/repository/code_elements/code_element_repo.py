from app.db.async_terminus_client import AsyncClient
from datetime import datetime, timezone

from typing import Any, Union, List, Tuple
import uuid
from terminusdb_client.woqlquery.woql_query import Doc, WOQLQuery as WQ

from app.core.model.nodes import ClassNode, FunctionNode
from app.core.model.schemas import (
    CallGroupSchema,
    CallSchema,
    ClassSchema,
    CodeContentSchema,
    CodeElementGroupSchema,
    CodePositionSchema,
    FunctionSchema,
)
from app.core.repository.base_repo import BaseRepo
from app.core.repository.utils import (
    CODE_CHILD_TYPE_TO_FIELD,
    CODE_ELEMENT_FIELDS,
    CODE_SET_FIELDS_TO_PRESERVE,
    build_path_field_name,
    parse_code_element_child,
    parse_structure_child,
)

_CODE_DESCENDANT_SCHEMA_BY_KIND = {
    "function": FunctionSchema.__name__,
    "class": ClassSchema.__name__,
    "call": CallSchema.__name__,
    "code_element_group": CodeElementGroupSchema.__name__,
    "call_group": CallGroupSchema.__name__,
}
_ALL_CODE_DESCENDANT_SCHEMAS = list(_CODE_DESCENDANT_SCHEMA_BY_KIND.values())

# Define a type for elements handled here
CodeNode = Union[FunctionNode, ClassNode]
CodeSchema = Union[FunctionSchema, ClassSchema]


class CodeElementRepo(BaseRepo[CodeNode, CodeSchema]):
    def __init__(self, client: AsyncClient):
        # We pass FunctionNode as default, but methods handle both
        super().__init__(client, FunctionNode, FunctionSchema)

    @staticmethod
    def _merge_update_fields(existing_raw: dict, _node: CodeNode, schema: CodeSchema):
        BaseRepo.merge_set_fields(
            schema, existing_raw, CODE_SET_FIELDS_TO_PRESERVE)

    def _to_schema(self, node: CodeNode) -> CodeSchema:
        if isinstance(node, FunctionNode):
            return FunctionSchema.from_pydantic(node)
        elif isinstance(node, ClassNode):
            return ClassSchema.from_pydantic(node)
        else:
            raise ValueError(f"Invalid node type: {type(node)}")

    async def update(self, node: CodeNode):
        return await self.update_node(
            node,
            commit_msg=f"Updating code element {node.id}",
            update_schema=self._merge_update_fields,
        )

    async def create(self, node: Union[CodeNode, List[CodeNode]], raw: bool = False):
        return await self.create_nodes(
            node,
            singular_name="code element",
            plural_name="code elements",
            raw=raw,
        )

    async def update_batch(self, nodes: List[CodeNode]):
        """Polymorphic update for both Classes and Functions."""
        if not nodes:
            return True

        items_raw = await self.get_by_ids([n.id for n in nodes], raw=True)
        id_to_raw = {r["@id"]: r for r in items_raw} if items_raw else {}

        schemas = []
        for node in nodes:
            existing_raw = id_to_raw.get(node.id)
            if not existing_raw:
                continue

            # Determine correct schema class
            schema_cls = FunctionSchema if isinstance(
                node, FunctionNode) else ClassSchema
            schema = schema_cls.from_pydantic(node)

            self._merge_update_fields(existing_raw, node, schema)
            self.touch_updated_at(schema)
            schemas.append(schema)

        if not schemas:
            return None
        return await self.client.update_document(schemas, commit_msg=f"Updating {len(schemas)} elements")

    async def delete(self, item_id: str):
        # Cleans up both possible parent link fields
        return await self.delete_with_parent_cleanup(
            item_id,
            parent_field="function_children|class_children",
            commit_msg=f"Deleting code element {item_id}",
        )

    async def get_children(self, parent_id: str, child_types: list[str]):
        field_name = build_path_field_name(
            child_types, CODE_ELEMENT_FIELDS, type_to_field=CODE_CHILD_TYPE_TO_FIELD
        )
        return await self.get_children_by_path(
            parent_id,
            field_name,
            parse_code_element_child,
            allowed_path_fields=CODE_ELEMENT_FIELDS,
        )

    async def get_code_descendant_nodes(
        self,
        parent_id: str,
        child_types: list[str],
        depth_start: int | None = None,
        depth_max: int | None = None,
    ) -> tuple[list[Any], dict[str, dict[str, Any]]]:
        """
        Descendants of ``parent_id`` along code edges. Path depth uses WOQL
        ``{depth_start, depth_max}`` (omit both for ``+``). Result is deduped by
        id and sorted by id for stable tree building.

        The second value maps callee document id -> raw document for
        ``TreeBuilder`` (from the same WOQL query as descendants).
        """
        if child_types:
            filtered = [
                n
                for k in child_types
                if (n := _CODE_DESCENDANT_SCHEMA_BY_KIND.get(k)) is not None
            ]
            if not filtered:
                return [], {}
        else:
            filtered = list(_ALL_CODE_DESCENDANT_SCHEMAS)

        field_name = build_path_field_name(
            child_types, CODE_ELEMENT_FIELDS, type_to_field=CODE_CHILD_TYPE_TO_FIELD
        )
        nodes, target_lookup = await self.get_children_by_path(
            parent_id,
            field_name,
            parse_code_element_child,
            filtered_types=filtered,
            allowed_path_fields=CODE_ELEMENT_FIELDS,
            depth_start=depth_start,
            depth_max=depth_max,
            include_call_target_docs=True,
        )
        by_id: dict[str, Any] = {}
        for n in nodes:
            if n is None:
                continue
            nid = getattr(n, "id", None)
            if nid:
                by_id[str(nid)] = n
        ordered = [by_id[k] for k in sorted(by_id.keys())]
        return ordered, target_lookup

    async def move_item(self, new_parent_id: str, item_id: str, child_type: str):
        return await self.move_item_by_type(
            new_parent_id,
            item_id,
            child_type,
            child_type_to_field=CODE_CHILD_TYPE_TO_FIELD,
        )

    async def move_batch(self, moves: List[Tuple[str, str, str]]):
        return await self.move_batch_by_type(moves, child_type_to_field=CODE_CHILD_TYPE_TO_FIELD)

    async def flush_batch(
        self,
        insert: List[FunctionNode | ClassNode],
        code_update: List[FunctionNode | ClassNode],
        update_content: List[Tuple[str, str]],
        delete: List[str],
        move: List[Tuple[str, str, str]],
        max_queries_per_commit: int | None = None,
    ):
        if (
            not insert
            and not code_update
            and not update_content
            and not delete
            and not move
        ):
            return True

        queries = []
        updated_at = datetime.now(timezone.utc)

        for node in code_update:
            # Generate unique suffix for this iteration's variables (UUID without hyphens)
            suffix = str(uuid.uuid4()).replace("-", "")
            parent_id = node.id

            # Build sub-queries list
            sub_queries = []

            # 1. Code Position Update (delete old, insert new)
            code_pos_schema = CodePositionSchema.from_pydantic(

                node.code_position)

            new_code_pos_dict = code_pos_schema._obj_to_dict()[0]

            new_code_pos_dict["@type"] = "CodePositionSchema"
            new_code_pos_dict["@linked-by"] = {

                "@id": parent_id,

                "@property": "code_position"

            }

            sub_queries.extend([
                # Find old code_position
                WQ().triple(parent_id, "code_position", "v:old_code_pos"+parent_id),
                # Delete old subdocument
                WQ().delete_document("v:old_code_pos"+parent_id),
                # Insert new subdocument
                WQ().insert_document(Doc(new_code_pos_dict), "v:new_code_pos"+parent_id),
                # Update parent's link

                WQ().update_triple(parent_id, "code_position", "v:new_code_pos"+parent_id),
            ])

            # 2. Update qname (delete old if exists, add new)
            sub_queries.extend([
                WQ().opt(
                    WQ().woql_and(
                        WQ().triple(parent_id, "qname",
                                    f"v:old_qname_{suffix}"),
                        WQ().delete_triple(parent_id,
                                           "qname", f"v:old_qname_{suffix}")
                    )
                ),
                WQ().add_triple(parent_id, "qname", WQ().string(node.qname)),
            ])

            # 3. Update updated_at (delete old if exists, add new)
            sub_queries.extend([
                WQ().opt(
                    WQ().woql_and(
                        WQ().triple(parent_id, "updated_at",
                                    f"v:old_updated_{suffix}"),
                        WQ().delete_triple(parent_id,
                                           "updated_at", f"v:old_updated_{suffix}")
                    )
                ),
                WQ().add_triple(parent_id, "updated_at", updated_at),
            ])

            # 4. Handle base_classes for ClassNode (REPLACE the entire set)
            if isinstance(node, ClassNode) and hasattr(node, 'base_classes'):

                for base_class in node.base_classes:
                    sub_queries.append(
                        WQ().add_triple(parent_id, "base_classes", WQ().string(base_class))
                    )

            # Combine all into one atomic query for this node
            query = WQ().woql_and(*sub_queries)
            queries.append(query)
            # break

        for node in insert:

            if isinstance(node, FunctionNode):
                schema = FunctionSchema.from_pydantic(node)._obj_to_dict()[0]
            elif isinstance(node, ClassNode):
                schema = ClassSchema.from_pydantic(node)._obj_to_dict()[0]

            else:
                raise ValueError(f"Invalid node type: {type(node)}")

            queries.append(WQ().insert_document(Doc(schema)))

        # build delete operations
        for delete_id in delete:
            field = "function_children"
            if delete_id.startswith("ClassSchema"):
                field = "class_children"
            queries.append(WQ().woql_and(
                WQ().opt(
                    WQ().triple("v:parent", field, delete_id)
                    .delete_triple("v:parent", field, delete_id)
                ),
                WQ().delete_document(delete_id)
            ))
            # build insert operations

        for file_id, content in update_content:
            schemas = CodeContentSchema.from_file_content(file_id, content)

            queries.append(WQ().update_document(
                Doc(schemas._obj_to_dict()[0])))

        for item_id, new_parent_id, child_type in move:
            field = CODE_CHILD_TYPE_TO_FIELD.get(
                child_type, "function_children")

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

        limit = max_queries_per_commit or len(queries)
        if limit <= 0:
            limit = len(queries)

        total_chunks = (len(queries) + limit - 1) // limit
        ok = True
        for start in range(0, len(queries), limit):
            chunk = queries[start: start + limit]
            chunk_no = start // limit + 1
            combined = WQ().woql_and(*chunk)
            try:
                result = await self.client.query(
                    combined,
                    commit_msg=(
                        f"code_element batch {chunk_no}/{total_chunks}: "
                        f"{len(chunk)} ops ({len(insert)} inserts, {len(delete)} deletes, {len(move)} moves)"
                    ),
                )
                print(result)
            except Exception as exc:
                print(f"Batch operation failed: {exc}")
                ok = False
                break
        return ok

    async def get_node_lineage(self, node_id: str) -> list[Any]:
        query = WQ().select("v:target_doc").woql_and(
            WQ().eq("v:node", node_id).
            path("v:node", "(<function_children|<class_children|<file_children|<folder_children|<structure_group|<code_element_group)*", "v:parent").
            read_document("v:parent", "v:target_doc")
        )
        try:
            result = await self.client.query(query)
            print(f"result: {result}")
        except Exception as exc:
            print(f"error-", exc)

            return []

        bindings = result.get("bindings") or []
        docs: list[dict[str, Any]] = []
        for row in bindings:
            doc = row.get("target_doc")
            if not isinstance(doc, dict):
                continue

            docs.append(parse_structure_child(doc))

        if not docs:
            return []

        return docs
