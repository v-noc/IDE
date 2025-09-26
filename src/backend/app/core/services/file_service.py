from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import FileNode


class FileService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos

    def create(self, name: str, qname: str, description: str, path: str):
        file = FileNode(
            name=name,
            qname=qname,
            description=description,
            path=path,
        )
        return self.repos.file_repo.create(file)

    def get(self, file_id: str):
        return self.repos.file_repo.get_by_id(file_id)

    def update(self, file: FileNode):
        return self.repos.file_repo.update(file.key, file)

    def delete(self, file_key: str):
        return self.repos.file_repo.delete(file_key)

    def add_function(self, file_id: str, function_id: str):
        return self.add_child_to_container(file_id, function_id, "file_to_function")

    def add_call(self, file_id: str, call_id: str):
        return self.add_child_to_container(file_id, call_id, "file_to_call")

    def add_class(self, file_id: str, class_id: str):
        return self.add_child_to_container(file_id, class_id, "file_to_class")

    def get_children(self, file_id: str):
        return self.repos.file_repo.get_containment_tree(file_id)
