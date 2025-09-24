from app.core.repository import Repositories
from app.core.model.nodes import ProjectNode
from app.core.services.container_service import ContainerService
from app.models.properties import ThemeConfig


class ProjectService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos

    def create_project(self, name: str, path: str):
        project = ProjectNode(
            name=name,
            path=path,
            theme_config=ThemeConfig()
        )
        return self.repos.nodes.create(project)

    def get_project(self, project_id: str):
        return self.repos.project_repo.get_by_id(project_id)

    def get_all_projects(self):
        return self.repos.project_repo.get_all_projects()

    def add_folder_to_project(self, project_id: str, folder_id: str):
        return self.add_child_to_container(project_id, folder_id, "project_to_folder")

    def add_file_to_project(self, project_id: str, file_id: str):
        return self.add_child_to_container(project_id, file_id, "project_to_file")
