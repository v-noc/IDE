from app.core.repository import Repositories
from app.core.model.nodes import ProjectNode
# from app.core.services.container_service import ContainerService
from app.db.context import ProjectUoW


class ProjectService():
    def __init__(self, uow: ProjectUoW):
        self.uow = uow
        self.project_repos = self.uow.get_project_repos()
        self.meta_repos = self.uow.get_meta_repos()

    async def delete(self, project_id: str):
        return await self.meta_repos.project_repo.delete(project_id)

    async def update(self, project: ProjectNode):
        return await self.meta_repos.project_repo.update(project.id, project)

    async def create_node(self, project: ProjectNode):
        return await self.meta_repos.project_repo.create(project)

    async def create(self, name: str, description: str, path: str):
        return await self.meta_repos.project_repo.create(name, description, path)

    async def get(self, project_id: str):
        return await self.meta_repos.project_repo.get_by_id(project_id)

    async def get_all(self):
        return await self.meta_repos.project_repo.get_all()

    async def get_children(self, exclude_types: list[str] = [], depth: int | str = 50):
        return await self.project_repos.project_repo.get_children(
            exclude_types,
        )
