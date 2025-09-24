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
