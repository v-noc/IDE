from app.db.context import ProjectUoW
from app.core.model.nodes import ThemeConfig


class ContainerService:
    def __init__(self, uow: ProjectUoW):
        self.uow = uow
        self.repos = self.uow.get_project_repos()

    async def update_basic_info(self, container_id: str, name: str, description: str, icon: str):
        return await self.repos.container_repo.update_basic_info(container_id, name, description, icon)

    async def update_theme_config(self, container_id: str, theme_config: ThemeConfig):
        return await self.repos.container_repo.update_theme_config(container_id, theme_config)
