from app.core.repository import Repositories
from app.core.model.nodes import ProjectNode
from app.core.services.container_service import ContainerService


class ProjectService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos

    async def delete(self, project: ProjectNode):
        return await self.repos.project_repo.delete(project.key)

    async def update(self, project: ProjectNode):
        return await self.repos.project_repo.update(project.key, project)

    async def create_node(self, project: ProjectNode):
        return await self.repos.project_repo.create(project)

    async def create(self, name: str, description: str, path: str):
        project = ProjectNode(
            name=name,
            qname=name.lower().replace(" ", "_"),
            description=description,
            path=path,
            theme_config=None,
        )
        return await self.repos.project_repo.create(project)

    async def get(self, project_id: str):
        return await self.repos.project_repo.get_by_id(project_id)

    async def get_all(self):
        return await self.repos.project_repo.get_all_projects()

    async def add_folder(self, project_id: str, folder_id: str):
        return await self.add_child_to_container(
            project_id,
            folder_id,
            "project_to_folder",
        )

    async def add_file(self, project_id: str, file_id: str):
        return await self.add_child_to_container(
            project_id,
            file_id,
            "project_to_file",
        )

    async def get_children(self, project_id: str, exclude_groups: bool = False):
        exclude_types = ["group"] if exclude_groups else None
        return await self.repos.project_repo.get_containment_tree(
            project_id,
            50,
            exclude_types=exclude_types,
        )

    async def get_project_structure(
        self,
        project_id: str,
        exclude_groups: bool = False,
    ):
        exclude_types = ["group"] if exclude_groups else None
        return await self.repos.project_repo.get_containment_tree(
            project_id,
            depth="*",
            exclude_types=exclude_types,
        )
