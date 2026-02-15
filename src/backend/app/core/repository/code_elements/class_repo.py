from datetime import datetime, timezone
from typing import Literal
from app.db.async_terminus_client import AsyncClient
from app.db.async_terminus_client import WOQLQuery as WQ
from app.core.model.schemas import ClassSchema
from app.core.model.nodes import ClassNode
from app.core.repository.utils import (
    parse_code_element_child,
    build_path_field_name,
    CODE_ELEMENT_FIELDS,
)


class ClassRepo():
    def __init__(self, client: AsyncClient):
        self.client = client

    async def create(self, class_node: ClassNode, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        class_schema = ClassSchema.from_pydantic(class_node)

        await self.client.insert_document(
            class_schema, commit_msg=f"Creating class {class_node.name}"
        )
        if current_db:
            await self.client.set_db(current_db)
        return class_schema.to_pydantic()

    async def get_by_id(self, class_id: str, project_db_name: str, raw: bool = False):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            class_schema = await self.client.get_document(class_id)
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)
        if raw:
            return class_schema
        return ClassNode.from_raw_dict(class_schema)

    async def delete(self, class_id: str, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            query = WQ().woql_and(
                WQ().opt(
                    WQ().triple("v:parent", "class_children", class_id)
                    .delete_triple("v:parent", "class_children", class_id)
                ),
                WQ().delete_document(class_id)
            )
            await self.client.query(query, commit_msg=f"Deleting class {class_id}")
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return True

    async def update(self, class_node: ClassNode, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        class_raw = await self.get_by_id(class_node.id, project_db_name, raw=True)
        if not class_raw:
            return None
        class_schema = ClassSchema.from_pydantic(class_node)

        class_schema.class_children = class_raw.get("class_children", set())
        class_schema.function_children = class_raw.get("function_children", set())
        class_schema.call_children = class_raw.get("call_children", set())
        class_schema.code_element_group = class_raw.get(
            "code_element_group", set()
        )
        class_schema.call_group = class_raw.get("call_group", set())
        class_schema.documents = class_raw.get("documents", set())
        class_schema.theme_config = class_raw.get("theme_config")

        class_schema.updated_at = datetime.now(timezone.utc)
        try:
            await self.client.update_document(
                class_schema, commit_msg=f"Updating class {class_node.id}"
            )
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return class_schema.to_pydantic()

    async def get_children(
        self, class_id: str, child_type: list[str], project_db_name: str
    ):
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
                    WQ().eq("v:start", class_id)
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
        item_type: Literal[
            "function", "class", "call", "code_element_group", "call_group"
        ],
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
