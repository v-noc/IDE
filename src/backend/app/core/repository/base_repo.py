from contextlib import asynccontextmanager
from datetime import datetime, timezone
from time import time
from typing import Any, Callable, Generic, Optional, Type, TypeVar
import uuid

from app.db.async_terminus_client import AsyncClient
from app.db.async_terminus_client import WOQLQuery as WQ

TNode = TypeVar("TNode")
TSchema = TypeVar("TSchema")


class BaseRepo(Generic[TNode, TSchema]):
    """Shared repository primitives for DB session and CRUD helpers."""

    def __init__(self, client: AsyncClient, node_class: Type[TNode], schema_class: Type[TSchema]):
        self.client = client
        self.node_class = node_class
        self.schema_class = schema_class

    @asynccontextmanager
    async def session(self, project_db_name: str, branch_name: Optional[str] = None):
        current_db = self.client.db
        new_client = None
        try:
            if current_db != project_db_name or self.client.branch != branch_name:
                new_client = self.client.clone()
                if branch_name:
                    new_client.branch = branch_name

                await new_client.set_db(project_db_name)
                yield new_client
            else:
                yield self.client
        finally:
            if new_client:
                # await new_client.close()
                del new_client

    def _to_schema(self, node: TNode) -> TSchema:
        return self.schema_class.from_pydantic(node)

    def _to_node(self, raw_data: dict[str, Any]) -> TNode:
        return self.node_class.from_raw_dict(raw_data)

    @staticmethod
    def _ensure_list(item_or_list: Any) -> list[Any]:
        if isinstance(item_or_list, list):
            return item_or_list
        return [item_or_list]

    async def create_nodes(
        self,
        node_or_nodes: TNode | list[TNode],
        project_db_name: str,
        singular_name: str,
        plural_name: str,
        raw: bool = False,
        branch_name: Optional[str] = None,
    ) -> TNode | list[TNode] | list[TSchema]:
        nodes = self._ensure_list(node_or_nodes)
        schemas = [self._to_schema(node) for node in nodes]

        if len(nodes) == 1 and not isinstance(node_or_nodes, list):
            commit_msg = f"Creating {singular_name} {nodes[0].name}"
        else:
            commit_msg = f"Creating {plural_name} {', '.join([node.name for node in nodes[:10]])}"

        async with self.session(project_db_name, branch_name=branch_name) as new_client:

            try:
                result = await new_client.insert_document(schemas, commit_msg=commit_msg)
                print(result)
            except Exception as exc:
                print("error inserting document", exc)
                return None

        if raw:
            return schemas
        if len(schemas) == 1 and not isinstance(node_or_nodes, list):
            return schemas[0].to_pydantic()
        return [schema.to_pydantic() for schema in schemas]

    async def get_by_id(self, item_id: str, project_db_name: str, raw: bool = False, branch_name: Optional[str] = None):
        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                item_raw = await new_client.get_document(item_id)
            except Exception as exc:
                print(exc)
                return None
        if raw:
            return item_raw
        return self._to_node(item_raw)

    async def get_by_ids(self, item_ids: list[str], project_db_name: str, raw: bool = False, branch_name: Optional[str] = None):
        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                items_raw = await new_client.get_documents(item_ids)
            except Exception as exc:
                print(exc)
                return [] if not raw else None
        if raw:
            return items_raw

        return [self._to_node(item_raw) for item_raw in items_raw]

    async def get_all(self, project_db_name: str, branch_name: Optional[str] = None) -> list[TNode]:
        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                items_raw = await new_client.get_all_documents(doc_type=self.schema_class.__name__)
            except Exception as exc:
                print(exc)
                return []
        items: list[TNode] = []
        for item_raw in items_raw:
            node = self._to_node(item_raw)
            if node is not None:
                items.append(node)
        return items

    @staticmethod
    def merge_fields(schema: TSchema, existing_raw: dict[str, Any], field_names: list[str]):
        for field in field_names:
            setattr(schema, field, existing_raw.get(field))

    @staticmethod
    def merge_set_fields(schema: TSchema, existing_raw: dict[str, Any], field_names: list[str]):
        for field in field_names:
            setattr(schema, field, existing_raw.get(field, set()))

    @staticmethod
    def touch_updated_at(schema: TSchema):
        schema.updated_at = datetime.now(timezone.utc)

    async def update_node(
        self,
        node: TNode,
        project_db_name: str,
        commit_msg: str,
        update_schema: Callable[[dict[str, Any], TNode, TSchema], None] = None,
        branch_name: Optional[str] = None,
    ):
        existing_raw = await self.get_by_id(node.id, project_db_name, raw=True)
        if not existing_raw:
            return None

        schema = self._to_schema(node)
        if update_schema:
            update_schema(existing_raw, node, schema)
        self.touch_updated_at(schema)

        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                await new_client.update_document(schema, commit_msg=commit_msg)
            except Exception as exc:
                print(exc)
                return None
        return schema.to_pydantic()

    async def update_nodes(
        self,
        nodes: list[TNode],
        project_db_name: str,
        commit_msg: str,
        update_schema: Callable[[dict[str, Any], TNode, TSchema], None],
        branch_name: Optional[str] = None,
    ) -> bool | None:
        existing_raw_items = await self.get_by_ids([node.id for node in nodes], project_db_name, raw=True)
        if not existing_raw_items:
            return None

        schemas: list[TSchema] = []
        for existing_raw, node in zip(existing_raw_items, nodes):
            schema = self._to_schema(node)
            update_schema(existing_raw, node, schema)
            self.touch_updated_at(schema)
            schemas.append(schema)

        if len(schemas) != len(nodes):
            print(f"Error updating nodes: {len(schemas)} != {len(nodes)}")
            return None

        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                await new_client.update_document(schemas, commit_msg=commit_msg)

            except Exception as exc:
                print(exc)
                return False
        return True

    async def delete_with_parent_cleanup(
        self,
        item_id: str,
        parent_field: str,
        project_db_name: str,
        commit_msg: str,
        branch_name: Optional[str] = None,
    ) -> bool:
        query = WQ().woql_and(
            WQ().opt(
                WQ().triple("v:parent", parent_field, item_id).delete_triple(
                    "v:parent", parent_field, item_id)
            ),
            WQ().delete_document(item_id),
        )
        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                await new_client.query(query, commit_msg=commit_msg)
            except Exception as exc:
                print(exc)
                return False
        return True

    async def delete_batch_with_parent_cleanup(
        self,
        item_ids: list[str],
        parent_field: str,
        binding_var: str,
        project_db_name: str,
        commit_msg: str,
        branch_name: Optional[str] = None,
    ) -> bool:
        query = WQ().member(binding_var, item_ids).woql_and(
            WQ().opt(
                WQ()
                .triple("v:parent", parent_field, binding_var)
                .delete_triple("v:parent", parent_field, binding_var)
            ),
            WQ().delete_document(binding_var),
        )
        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                await new_client.query(query, commit_msg=commit_msg)
            except Exception as exc:
                print(exc)
                return False
        return True

    async def get_children_by_path(
        self,
        parent_id: str,
        field_name: str,
        parse_child: Callable[[dict[str, Any]], Any],
        project_db_name: str,
        filtered_types: list[str] | None = None,
        allowed_path_fields: tuple[str, ...] | None = None,
        branch_name: Optional[str] = None,
    ):
        if allowed_path_fields is not None:
            requested_fields = field_name.strip("()").split("|")
            if any(field not in allowed_path_fields for field in requested_fields):
                return []

        query_step = (
            WQ()
            .eq("v:start", parent_id)
            .path("v:start", f"{field_name}+", "v:child")
        )
        if filtered_types:
            schema_types = [
                f"@schema:{schema_type}" for schema_type in filtered_types]
            query_step = (
                query_step
                .triple("v:child", "rdf:type", "v:type")
                .member("v:type", schema_types)
            )

        query = (
            WQ()
            .select("v:child_doc")
            .woql_and(
                query_step.read_document("v:child", "v:child_doc")
            )
        )
        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                result = await new_client.query(query)

            except Exception as exc:
                print(exc)
                return []

        children = []
        allowed_types = set(filtered_types or [])
        for child_raw in [row["child_doc"] for row in result["bindings"]]:
            node = parse_child(child_raw)
            if node is not None:
                children.append(node)
        return children

    async def move_item_by_type(
        self,
        new_parent_id: str,
        item_id: str,
        child_type: str,
        child_type_to_field: dict[str, str],
        project_db_name: str,
        branch_name: Optional[str] = None,
    ) -> bool | None:
        field_name = child_type_to_field.get(child_type)
        if not field_name:
            return None

        current_time = datetime.now(timezone.utc)
        query = WQ().woql_and(
            WQ().opt(
                WQ()
                .triple("v:parent", field_name, item_id)
                .delete_triple("v:parent", field_name, item_id)
                .update_triple("v:parent", "updated_at", current_time)
            ),
            WQ().add_triple(new_parent_id, field_name, item_id).opt(
                WQ().triple("v:parent", "updated_at", current_time).
                update_triple("v: parent", "updated_at", current_time),
            )
        )

        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                await new_client.query(query, commit_msg=f"Moving item {item_id} to {new_parent_id}")
            except Exception as exc:
                print(exc)
                return False
        return True

    # moves is a list of tuples (item_id, parent_id, child_type)
    async def move_batch_by_type(
        self,
        moves: list[tuple[str, str, str]],
        child_type_to_field: dict[str, str],
        project_db_name: str,
        branch_name: Optional[str] = None,
    ) -> bool:
        parsed_data: dict[str, dict[str, set[str]]] = {}
        current_time = datetime.now(timezone.utc)
        queries = []
        for item_id, parent_id, child_type in moves:
            field_name = child_type_to_field.get(child_type)
            if not field_name:
                raise ValueError(f"Invalid child type: {child_type}")
            if parent_id not in parsed_data:
                parsed_data[parent_id] = {
                    field: set() for field in set(child_type_to_field.values())}
            parsed_data[parent_id][field_name].add(item_id)

        for parent_id, fields in parsed_data.items():
            for field_name, item_ids in fields.items():
                if not item_ids:
                    continue
                query = WQ().member("v:item", list(item_ids)).woql_and(
                    WQ().opt(
                        WQ()
                        .triple("v:parent", field_name, "v:item")
                        .delete_triple("v:parent", field_name, "v:item")
                    ),

                    WQ().add_triple(parent_id, field_name, "v:item").opt(
                        WQ().triple("v:parent", "updated_at", current_time).update_triple(
                            "v:parent", "updated_at", current_time
                        )
                    )
                )
                queries.append(query)

        if not queries:
            return True

        async with self.session(project_db_name, branch_name=branch_name) as new_client:
            try:
                query = WQ().woql_or(*queries)
                parent_ids = "Moving items to multiple parents"

                await new_client.query(query, commit_msg=f"Moving items to {parent_ids}")

            except Exception as exc:
                print(f"error {exc}")
                return False
        return True

    async def find(self, field: str, values: list[str], project_db_name: str) -> list[TNode]:
        if not field or not values:
            return []

        query = (
            WQ()
            .select("v:item_doc")
            .woql_and(
                WQ().member("v:value", [WQ().string(value)
                                        for value in values]),
                WQ().triple("v:item", field, "v:value"),
                WQ().triple("v:item", "rdf:type",
                            f"@schema:{self.schema_class.__name__}"),
                WQ().read_document("v:item", "v:item_doc"),
            )
        )

        async with self.session(project_db_name) as new_client:
            try:
                result = await new_client.query(query)

            except Exception as exc:
                print(exc)
                return []
        nodes: list[TNode] = []
        for item_raw in [row["item_doc"] for row in result["bindings"]]:
            node = self._to_node(item_raw)
            if node is not None:
                nodes.append(node)
        return nodes

    async def get_by_qnames(self, qnames: list[str], project_db_name: str) -> list[TNode]:
        """Return nodes whose qname is in the given list."""
        if not qnames:
            return []
        query = (
            WQ()
            .select("v:item_doc")
            .woql_and(
                WQ().member("v:qname", [WQ().string(x) for x in qnames]),
                WQ().triple("v:item", "qname", "v:qname"),
                WQ().triple("v:item", "rdf:type",
                            f"@schema:{self.schema_class.__name__}"),
                WQ().read_document("v:item", "v:item_doc"),
            )
        )

        async with self.session(project_db_name) as new_client:
            try:
                result = await new_client.query(query)

            except Exception as exc:
                print(exc)
                return []

        nodes: list[TNode] = []
        for item_raw in [row["item_doc"] for row in result["bindings"]]:
            node = self._to_node(item_raw)
            if node is not None:
                nodes.append(node)
        return nodes
