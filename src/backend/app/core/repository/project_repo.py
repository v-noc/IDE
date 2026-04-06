from datetime import datetime
from datetime import timezone
from app.db.errors import DatabaseError
from app.db.async_terminus_client import WOQLQuery as WQ
from app.db.async_terminus_client import AsyncClient
from app.core.model.schemas import ProjectSchema
from app.core.model import ProjectNode

from app.core.repository.project_bootstrap import bootstrap_empty_project_database
from app.core.repository.utils import parse_structure_child
from app.core.model.schemas import FileSchema, FolderSchema, FunctionSchema, ClassSchema, CallSchema, CodeElementGroupSchema, CallGroupSchema, StructureGroupSchema

# Full flat graph for TreeBuilder / graph jobs; structure-only for initial dashboard load.
PROJECT_FULL_GRAPH_TYPES = frozenset({
    FileSchema.__name__,
    FolderSchema.__name__,
    FunctionSchema.__name__,
    ClassSchema.__name__,
    CallSchema.__name__,
    CodeElementGroupSchema.__name__,
    CallGroupSchema.__name__,
    StructureGroupSchema.__name__,
})
PROJECT_STRUCTURE_TYPES = frozenset({
    FileSchema.__name__,
    FolderSchema.__name__,
    StructureGroupSchema.__name__,
})


class ProjectRepo():
    def __init__(self, client: AsyncClient):
        self.client = client

    async def delete(self, project_id: str):
        project = await self.get_by_id(project_id)
        if project is None:

            return True

        clone_client = self.client.clone()

        try:
            await clone_client.delete_database(project["db_name"], team="admin")
            await self.client.delete_document(project, commit_msg=f"Deleting project {project_id}")

            return True
        except DatabaseError as e:

            if e.error_obj.get("api.error", {}).get("@type", "") == "api:DatabaseNotFound":
                raise ValueError(f"Database {project_id} not found")
            else:
                raise e

    async def register_project(
        self,
        name: str,
        description: str,
        path: str,
        db_name: str,
    ) -> ProjectNode:
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
        return ProjectNode(
            id=project._id,
            name=project.name,
            description=project.description,
            local_path=project.local_path,
            db_name=project.db_name,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    async def create(self, name, description, path):
        db_name = await bootstrap_empty_project_database(
            self.client.clone(),
            name,
            description,
        )
        return await self.register_project(name, description, path, db_name)

    async def get_by_id(self, project_id: str):
        try:
            result = await self.client.get_document(project_id)

            return result
        except DatabaseError as e:
            print(e, " ", project_id)
            if e.error_obj.get("api:error", {}).get("@type", "") == "api:DocumentNotFound":
                return None
            else:
                raise e
        except Exception as e:
            print(f"error getting project by id: {e}")
            return None

    async def get_all(self):
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

    async def update(self, project_id: str, project: ProjectNode):
        old_project = await self.get_by_id(project_id)
        if not old_project:
            return None

        old_project["name"] = project.name
        old_project["description"] = project.description
        old_project["local_path"] = project.local_path

        old_project["updated_at"] = datetime.now(timezone.utc)

        await self.client.update_document(old_project, commit_msg=f"Updating project {project_id}")
        return ProjectNode(
            id=old_project["@id"],
            name=old_project["name"],
            description=old_project["description"],
            local_path=old_project["local_path"],
            db_name=old_project["db_name"],
            created_at=old_project["created_at"],
            updated_at=old_project["updated_at"],
        )

    async def _query_documents_by_schema_types(
        self,
        include_types: frozenset[str],
        exclude_types: list[str],
        include_commit_id: bool,
    ):
        filtered_types = set(include_types) - set(exclude_types)
        if not filtered_types:
            return [], None

        try:
            query = WQ().select("v:doc").woql_and(
                WQ().triple("v:uri", "rdf:type", "v:type"),
                WQ().member(
                    "v:type",
                    [f"@schema:{t}" for t in filtered_types],
                ),
                WQ().read_document("v:uri", "v:doc"),
            )
            result, version = await self.client.query(query, get_data_version=True)
            children = []
            for doc in [row["doc"] for row in result["bindings"]]:
                if doc.get("@type") == "FolderSchema" and doc.get("is_root") == "true":
                    continue
                children.append(parse_structure_child(doc))

            if include_commit_id:
                return children, version
            return children, None
        except Exception as e:
            print(e)
            return [], None

    async def get_structure(self, exclude_types: list[str] = [], include_commit_id: bool = False):
        """Folders, files, and structure groups only (no functions/classes/calls)."""
        return await self._query_documents_by_schema_types(
            PROJECT_STRUCTURE_TYPES,
            exclude_types,
            include_commit_id,
        )

    async def get_children(self, exclude_types: list[str] = [], include_commit_id: bool = False):
        """All graph document types used by TreeBuilder (minus exclude_types)."""
        return await self._query_documents_by_schema_types(
            PROJECT_FULL_GRAPH_TYPES,
            exclude_types,
            include_commit_id,
        )
