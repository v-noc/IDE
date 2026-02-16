from app.core.repository import Repositories
from app.core.model.nodes import ProjectNode
# from app.core.services.container_service import ContainerService


class ProjectService():
    def __init__(self, repos: Repositories):
        self.repos = repos

    async def delete(self, project_id: str):
        return await self.repos.project_repo.delete(project_id)

    async def update(self, project: ProjectNode):
        return await self.repos.project_repo.update(project.id, project)

    async def create_node(self, project: ProjectNode):
        return await self.repos.project_repo.create(project)

    async def create(self, name: str, description: str, path: str):
        return await self.repos.project_repo.create(name, description, path)

    async def add_folder(self, project_id: str, folder_id: str):
        return await self.add_child(project_id, folder_id)

    async def add_file(self, project_id: str, file_id: str):
        return await self.add_child(project_id, file_id)

    async def get(self, project_id: str):
        return await self.repos.project_repo.get_by_id(project_id)

    async def get_all(self):
        return await self.repos.project_repo.get_all()

    async def get_children(self, project_db_name: str, exclude_types: list[str] = [], depth: int | str = 50):

        return await self.repos.project_repo.get_children(
            project_db_name,
            exclude_types,
        )

    async def get_project_structure(
        self,
        project_id: str,
        exclude_groups: bool = False,
    ):
        return await self.get_children(project_id, exclude_groups=exclude_groups, depth="*")
