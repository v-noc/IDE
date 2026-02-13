
from app.db.async_terminus_client import AsyncClient


class FolderRepo():
    def __init__(self, client: AsyncClient):
        self.client = client

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

    def create_folder(self, parent_id: str, name: str, description: str):
        pass

    def update_folder(self, folder_id: str, name: str, description: str):
        pass

    def delete_folder(self, folder_id: str):
        pass
