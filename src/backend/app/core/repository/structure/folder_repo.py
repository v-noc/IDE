
from datetime import datetime, timezone
from app.db.async_terminus_client import AsyncClient
from app.core.model.nodes import FolderNode
from app.core.model.schemas import FolderSchema


class FolderRepo():
    def __init__(self, client: AsyncClient):
        self.client = client

    async def create(self, new_folder: FolderNode, project_db_name: str):

        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        folder_schema = FolderSchema(
            _id=new_folder.id,
            name=new_folder.name,
            description=new_folder.description,
            qname=new_folder.qname,
            path=new_folder.path,
            folder_children=new_folder.folder_children,
            file_children=new_folder.file_children,
            structure_group=new_folder.structure_group,
            created_at=new_folder.created_at,
            updated_at=new_folder.updated_at,
        )

        await self.client.insert_document(folder_schema, commit_msg=f"Creating folder {new_folder.name}")
        if current_db:
            await self.client.set_db(current_db)
        return folder_schema.to_pydantic()

    async def get_by_id(self, folder_id: str, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            folder_raw = await self.client.get_document(folder_id)
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)

        folder = FolderNode(
            id=folder_raw["@id"],
            name=folder_raw["name"],
            description=folder_raw["description"],
            qname=folder_raw["qname"],
            path=folder_raw["path"],
            folder_children=folder_raw.get("folder_children", set()),
            file_children=folder_raw.get("file_children", set()),
            structure_group=folder_raw.get("structure_group", set()),
            created_at=folder_raw["created_at"],
            updated_at=folder_raw["updated_at"],
        )
        return folder

    async def delete(self, folder_id: str, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            await self.client.delete_document(folder_id, commit_msg=f"Deleting folder {folder_id}")
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return True

    async def update(self, folder: FolderNode, project_db_name: str):
        current_db = None

        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        existing_folder = await self.get_by_id(folder.id, project_db_name)
        if not existing_folder:
            return None

        folder_schema = FolderSchema.from_pydantic(folder)
        folder_schema.updated_at = datetime.now(timezone.utc)

        try:
            await self.client.update_document(folder_schema, commit_msg=f"Updating folder {folder.id}")
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return folder_schema.to_pydantic()

    def get_folder_by_filed(self, field_name: str, field_value: str):
        pass

    def get_children(self, folder_id: str, child_type: str):
        pass

    def get_direct_children(self, folder_id: str, child_type: str):
        pass

    def move_item(self, item_id: str, new_parent_id: str, child_type: str):
        pass

    def add_child(self, parent_id: str, child_id: str, child_type: str):
        pass

    def remove_child(self, parent_id: str, child_id: str, child_type: str):
        pass
