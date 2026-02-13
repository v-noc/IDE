

from app.db.async_terminus_client import AsyncClient


class ProjectRepo():
    def __init__(self, client: AsyncClient):
        self.client = client

    def get_project_by_id(self, project_id: str):
        pass

    def get_all_projects(self):
        pass

    def create_project(self, project):
        pass

    def update_project(self, project_id: str, project):
        pass

    def delete_project(self, project_id: str):
        pass

    def get_children(self, project_id: str):
        pass
