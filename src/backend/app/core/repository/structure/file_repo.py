from datetime import datetime, timezone
from app.core.model.nodes import FileNode
from app.core.model.schemas import FileSchema
from app.db.async_terminus_client import AsyncClient
from app.db.async_terminus_client import WOQLQuery as WQ


class FileRepo():
    def __init__(self, client: AsyncClient):
        self.client = client

    async def create(self, file: FileNode, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        file_schema = FileSchema.from_pydantic(file)
        await self.client.insert_document(file_schema, commit_msg=f"Creating file {file.name}")
        if current_db:
            await self.client.set_db(current_db)
        return file_schema.to_pydantic()

    async def get_by_id(self, file_id: str, project_db_name: str, raw: bool = False):
        current_db = None

        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            file_raw = await self.client.get_document(file_id)
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)

        if raw:
            return file_raw
        return FileNode.from_raw_dict(file_raw)

    async def delete(self, file_id: str, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            query = WQ().woql_and(
                WQ().opt(
                    WQ().triple("v:parent", "file_children", file_id)
                    .delete_triple("v:parent", "file_children", file_id)
                ),
                WQ().delete_document(file_id)
            )
            await self.client.query(query, commit_msg=f"Deleting file {file_id}")
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return True

    async def update(self, file: FileNode, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        existing_file = await self.get_by_id(file.id, project_db_name, raw=True)
        if not existing_file:
            return None
        file_schema = FileSchema.from_pydantic(file)

        file_schema.call_children = existing_file.get("call_children", set())
        file_schema.call_group = existing_file.get("call_group", set())
        file_schema.class_children = existing_file.get("class_children", set())
        file_schema.function_children = existing_file.get(
            "function_children", set())
        file_schema.code_element_group = existing_file.get(
            "code_element_group", set())

        file_schema.updated_at = datetime.now(timezone.utc)
        try:
            await self.client.update_document(file_schema, commit_msg=f"Updating file {file.id}")
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return file_schema.to_pydantic()

    async def move_item(self, new_parent_id: str, item_id: str,  child_type: str, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        filed_name = None

        match child_type:
            case "folder":
                filed_name = "folder_children"
            case "file":
                filed_name = "file_children"
            case "structure_group":
                filed_name = "structure_group"
            case _:
                return None

        if not filed_name:
            raise ValueError(f"Invalid child type: {child_type}")

        try:
            current_time = datetime.now(timezone.utc)
            query = WQ().woql_and(
                WQ().opt(
                    WQ().triple("v:parent", filed_name, item_id)
                    .delete_triple("v:parent", filed_name, item_id)
                    .update_triple("v:parent", "updated_at", current_time)
                ),
                WQ().add_triple(new_parent_id, filed_name, item_id)
                .update_triple(new_parent_id, "updated_at", current_time)
            )
            await self.client.query(query, commit_msg=f"Moving item {item_id} to {new_parent_id}")

            return True
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)

    def add_child(self, parent_id: str, child_id: str, child_type: str):
        pass

    def remove_child(self, parent_id: str, child_id: str, child_type: str):
        pass
