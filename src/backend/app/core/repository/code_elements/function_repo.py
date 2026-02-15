from datetime import datetime, timezone
from typing import Literal
from app.db.async_terminus_client import AsyncClient
from app.db.async_terminus_client import WOQLQuery as WQ
from app.core.model.schemas import FunctionSchema
from app.core.model.nodes import FunctionNode
from app.core.repository.utils import (
    parse_code_element_child,
    build_path_field_name,
    CODE_ELEMENT_FIELDS,
)


class FunctionRepo():
    def __init__(self, client: AsyncClient):
        self.client = client

    async def create(self, function: FunctionNode, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        function_schema = FunctionSchema.from_pydantic(function)

        await self.client.insert_document(function_schema, commit_msg=f"Creating function {function.name}")
        if current_db:
            await self.client.set_db(current_db)
        return function_schema.to_pydantic()

    async def get_by_id(self, function_id: str, project_db_name: str, raw: bool = False):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            function_schema = await self.client.get_document(function_id)
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)
        if raw:
            return function_schema
        return FunctionNode.from_raw_dict(function_schema)

    async def delete(self, function_id: str, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            query = WQ().woql_and(
                WQ().opt(
                    WQ().triple("v:parent", "function_children", function_id)
                    .delete_triple("v:parent", "function_children", function_id)
                ),
                WQ().delete_document(function_id)
            )
            await self.client.query(query, commit_msg=f"Deleting function {function_id}")
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return True

    async def update(self, function: FunctionNode, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        function_raw = await self.get_by_id(function.id, project_db_name, raw=True)
        if not function_raw:
            return None
        function_schema = FunctionSchema.from_pydantic(function)

        function_schema.function_children = function_raw.get(
            "function_children", set())
        function_schema.class_children = function_raw.get(
            "class_children", set())
        function_schema.call_children = function_raw.get(
            "call_children", set())
        function_schema.code_element_group = function_raw.get(
            "code_element_group", set())
        function_schema.call_group = function_raw.get("call_group", set())
        function_schema.documents = function_raw.get("documents", set())
        function_schema.theme_config = function_raw.get("theme_config")

        function_schema.updated_at = datetime.now(timezone.utc)
        try:
            await self.client.update_document(function_schema, commit_msg=f"Updating function {function.id}")
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return function_schema.to_pydantic()

    async def get_children(self, function_id: str, child_type: list[str], project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        filed_name = build_path_field_name(child_type, CODE_ELEMENT_FIELDS)

        try:
            query = (
                WQ()
                .select("v:child_doc")
                .woql_and(
                    WQ().eq("v:start", function_id)
                    .path("v:start", f"{filed_name}+", "v:child")
                    .read_document("v:child", "v:child_doc")
                )
            )
            result = await self.client.query(query)
            children = []
            for child_raw in [row["child_doc"] for row in result["bindings"]]:
                node = parse_code_element_child(child_raw)
                if node is not None:
                    children.append(node)
            return children
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)

    async def move_item(
        self,
        new_parent_id: str,
        item_id: str,
        item_type: Literal["function", "class", "call", "code_element_group", "call_group"],
        project_db_name: str,
    ):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        filed_name = None
        match item_type:
            case "function":
                filed_name = "function_children"
            case "class":
                filed_name = "class_children"
            case "call":
                filed_name = "call_children"
            case "code_element_group":
                filed_name = "code_element_group"
            case "call_group":
                filed_name = "call_group"
            case _:
                return None

        if not filed_name:
            raise ValueError(f"Invalid item type: {item_type}")

        try:
            current_time = datetime.now(timezone.utc)
            query = WQ().woql_and(
                WQ().opt(
                    WQ().triple("v:parent", filed_name, item_id)
                    .delete_triple("v:parent", filed_name, item_id)
                    .update_triple("v:parent", "updated_at", current_time)
                ),
                WQ().add_triple(new_parent_id, filed_name, item_id).update_triple(
                    new_parent_id, "updated_at", current_time
                ),
            )
            await self.client.query(
                query, commit_msg=f"Moving item {item_id} to {new_parent_id}"
            )

            return True
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
