from app.core.repository import Repositories
from app.core.model.nodes import ProjectNode
from app.core.services.container_service import ContainerService


class ProjectService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos

    def delete(self, project_key: str):
        return self.repos.project_repo.delete(project_key)

    def update(self, project: ProjectNode):
        return self.repos.project_repo.update(project.key, project)

    def create(self, name: str, description: str, path: str):
        project = ProjectNode(
            name=name,
            qname=name.lower().replace(" ", "_"),
            description=description,
            path=path,
            theme_config=None
        )
        return self.repos.nodes.create(project)

    def get(self, project_id: str):
        return self.repos.project_repo.get_by_id(project_id)

    def get_all(self):
        return self.repos.project_repo.get_all_projects()

    def add_folder(self, project_id: str, folder_id: str):
        return self.add_child_to_container(project_id, folder_id, "project_to_folder")

    def add_file(self, project_id: str, file_id: str):
        return self.add_child_to_container(project_id, file_id, "project_to_file")

    def get_children(self, project_id: str):
        return self.repos.project_repo.get_containment_tree(project_id)
