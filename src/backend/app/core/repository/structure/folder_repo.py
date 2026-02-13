
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

        folder = FolderSchema(
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
        print(
            f"Creating folder {new_folder.file_children} in database {folder.file_children}")
        await self.client.insert_document(folder, commit_msg=f"Creating folder {new_folder.name}")
        if current_db:
            await self.client.set_db(current_db)
        return folder

    def get_folder_by_id(self, folder_id: str):
        pass

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
