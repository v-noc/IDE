from datetime import datetime
from datetime import timezone
from terminusdb_client.errors import DatabaseError

from app.db.async_terminus_client import AsyncClient
from app.core.model.schemas import ProjectSchema, ensure_schema
from app.core.model import ProjectNode
from slugify import slugify


class ProjectRepo():
    def __init__(self, client: AsyncClient):
        self.client = client

    async def delete(self, project_id: str):
        project = await self.get_project_by_id(project_id)
        current_db = self.client.db
        if not project:
            return True

        try:
            await self.client.delete_database(project["db_name"])
            await self.client.set_db(current_db)
            await self.client.delete_document(project, commit_msg=f"Deleting project {project_id}")
            return True
        except DatabaseError as e:
            if e.error_obj.get("api.error", {}).get("@type", "") == "api:DatabaseNotFound":
                raise ValueError(f"Database {project_id} not found")
            else:
                raise e

    async def create(self, name, description, path):

        current_db = self.client.db
        db_name = slugify(name)
        try:
            await self.client.create_database(db_name, label=db_name, description="V-NOC code analysis graph")
        except DatabaseError as e:
            if e.error_obj.get("api:error", {}).get("@type", "") == "api:DatabaseAlreadyExists":
                db_name = f"{db_name}_{datetime.now().strftime("%Y%m%d%H%M%S")}"
                await self.client.create_database(db_name, label=db_name, description="V-NOC code analysis graph")
            else:
                raise e

        await ensure_schema(self.client, f"{name} Schema", description, [f"{name} Team"])
        await self.client.set_db(current_db)
        print(f" current database {current_db}")

        project = ProjectSchema(
            _id=f"{db_name}",
            name=name,
            description=description,
            local_path=path,
            db_name=db_name,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await self.client.insert_document(project, commit_msg=f"Creating project {name}")

        project_node = ProjectNode(
            id=project._id,
            name=project.name,
            description=project.description,
            local_path=project.local_path,
            db_name=project.db_name,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        return project_node

    async def get_project_by_id(self, project_id: str):
        return await self.client.get_document(project_id)

    async def get_all_projects(self):
        projects_raw = await self.client.get_all_documents(
            doc_type=ProjectSchema.__name__)

        projects = []
        for project in projects_raw:
            projects.append(ProjectNode(
                id=project["@id"],
                name=project["name"],
                description=project["description"],
                local_path=project["local_path"],
                db_name=project["db_name"],
                created_at=project["created_at"],
                updated_at=project["updated_at"],
            ))

        return projects

    def create_project(self, project):
        pass

    def update_project(self, project_id: str, project):
        pass

    def get_children(self, project_id: str):
        pass
