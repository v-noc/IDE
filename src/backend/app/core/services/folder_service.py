from app.core.repository import Repositories
from app.core.services.container_service import ContainerService
from app.core.model.nodes import FolderNode


class FolderService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos

    def create(self, name: str, qname: str, description: str, path: str):
        folder = FolderNode(
            name=name,
            qname=qname,
            description=description,
            path=path,
        )
        return self.repos.folder_repo.create(folder)

    def get(self, folder_id: str):
        return self.repos.folder_repo.get_by_id(folder_id)

    def update(self, folder: FolderNode):
        print(f"Project being update ", folder)
        return self.repos.folder_repo.update(folder.key, folder)

    def delete(self, folder_key: str):
        folder_id = f"nodes/{folder_key}"

        descendants = self.repos.folder_repo.get_containment_tree(
            folder_id, depth="*")

        descendant_keys = [item["vertex"]["_key"] for item in descendants]

        for key in reversed(descendant_keys):
            self.repos.nodes.delete(key)

        return self.repos.folder_repo.delete(folder_key)

    def add_folder(self, parent_folder_id: str, folder_id: str):
        return self.add_child_to_container(parent_folder_id, folder_id, "folder_to_folder")

    def add_file(self, parent_folder_id: str, file_id: str):
        return self.add_child_to_container(parent_folder_id, file_id, "folder_to_file")

    def get_children(self, folder_id: str):
        return self.repos.folder_repo.get_containment_tree(folder_id)
