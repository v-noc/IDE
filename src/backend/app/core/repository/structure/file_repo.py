from datetime import datetime, timezone
from app.core.model.nodes import FileNode
from app.core.model.schemas import FileSchema
from app.db.async_terminus_client import AsyncClient


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

    async def get_by_id(self, file_id: str, project_db_name: str):
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

        file = FileNode(
            id=file_raw["@id"],
            name=file_raw["name"],
            description=file_raw["description"],
            qname=file_raw["qname"],
            path=file_raw["path"],
            hash=file_raw["hash"],
            class_children=file_raw.get("class_children", set()),
            function_children=file_raw.get("function_children", set()),
            code_element_group=file_raw.get("code_element_group", set()),
            call_group=file_raw.get("call_group", set()),
            call_children=file_raw.get("call_children", set()),
            created_at=file_raw["created_at"],
            updated_at=file_raw["updated_at"],
        )

        return file

    async def delete(self, file_id: str, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            await self.client.delete_document(file_id, commit_msg=f"Deleting file {file_id}")
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

        existing_file = await self.get_by_id(file.id, project_db_name)
        if not existing_file:
            return None
        file_schema = FileSchema.from_pydantic(file)
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

    def get_file_by_path(self, path: str):
        pass

    def get_file_by_qname(self, qname: str):
        pass

    def get_children(self, folder_id: str):
        pass

    def get_direct_children(self, file_id: str):
        pass

    def move_item(self, item_id: str, new_parent_id: str, child_type: str):
        pass

    def add_child(self, parent_id: str, child_id: str, child_type: str):
        pass

    def remove_child(self, parent_id: str, child_id: str, child_type: str):
        pass
