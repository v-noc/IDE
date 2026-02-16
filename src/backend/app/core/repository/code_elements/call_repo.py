from datetime import datetime, timezone
from typing import Literal
from app.db.async_terminus_client import AsyncClient
from app.core.model.nodes import CallNode
from app.core.model.schemas.code_element_schema import CallSchema
from app.db.async_terminus_client import WOQLQuery as WQ
from app.core.repository.utils.child_raw import build_path_field_name, parse_code_element_child


class CallRepo():
    def __init__(self, client: AsyncClient):
        self.client = client

    async def create(self, call: CallNode, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        call_schema = CallSchema.from_pydantic(call)

        await self.client.insert_document(call_schema, commit_msg=f"Creating call {call.name}")

        if current_db:
            await self.client.set_db(current_db)
        return call_schema.to_pydantic()

    async def get_by_id(self, call_id: str, project_db_name: str, raw: bool = False):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            call_schema = await self.client.get_document(call_id)
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)
        if raw:
            return call_schema
        return CallNode.from_raw_dict(call_schema)

    async def delete(self, call_id: str, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            query = WQ().woql_and(
                WQ().opt(
                    WQ().triple("v:parent", "call_children", call_id)
                    .delete_triple("v:parent", "call_children", call_id)
                ),
                WQ().delete_document(call_id)
            )
            await self.client.query(query, commit_msg=f"Deleting call {call_id}")
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return True

    async def update(self, call: CallNode, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        call_raw = await self.get_by_id(call.id, project_db_name, raw=True)
        if not call_raw:
            return None
        call_schema = CallSchema.from_pydantic(call)

        call_schema.call_children = call_raw.get("call_children", set())
        call_schema.call_group = call_raw.get("call_group", set())
        call_schema.target_function = call_raw.get("target_function")
        call_schema.documents = call_raw.get("documents", set())
        call_schema.theme_config = call_raw.get("theme_config")

        call_schema.updated_at = datetime.now(timezone.utc)
        try:
            await self.client.update_document(call_schema, commit_msg=f"Updating call {call.name}")
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return call_schema.to_pydantic()

    async def move_item(self, new_parent_id: str, item_id: str, item_type: Literal["call", "call_group"], project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        filed_name = None
        match item_type:
            case "call":
                filed_name = "call_children"
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
                WQ().add_triple(new_parent_id, filed_name, item_id)
                    .update_triple(new_parent_id, "updated_at", current_time),
            )
            await self.client.query(query, commit_msg=f"Moving call {item_id} to {new_parent_id}")
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return True

    async def get_children(self, call_id: str, child_type: list[Literal["call", "call_group"]], project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            filed_name = build_path_field_name(
                child_type, ["call_children", "call_group"])
            query = (
                WQ()
                .select("v:child_doc")
                .woql_and(
                    WQ().eq("v:start", call_id)
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
            return []
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return []

    def get_direct_children(self, call_id: str, child_type: str):
        pass
