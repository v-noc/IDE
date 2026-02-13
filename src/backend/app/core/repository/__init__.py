
from backend.app.db.async_terminus_client import AsyncClient


from .project_repo import ProjectRepo
from .structure.folder_repo import FolderRepo
from .structure.file_repo import FileRepo
from .code_elements.function_repo import FunctionRepo
from .code_elements.class_repo import ClassRepo
from .code_elements.call_repo import CallRepo
from .log_repo import LogRepository
from .document_repo import DocumentRepo
from .group_repo import GroupRepo


class Repositories:
    """A container for all repository instances."""

    def __init__(self, client: AsyncClient):
        # Generic Node Repo for mixed-type queries
        self.client = client

        # Specific Node Repos for type-specific operations
        self.project_repo = ProjectRepo(client)
        self.folder_repo = FolderRepo(client)
        self.file_repo = FileRepo(client)
        self.function_repo = FunctionRepo(client)
        self.class_repo = ClassRepo(client)
        self.call_repo = CallRepo(client)
        self.group_repo = GroupRepo(client)
        self.log_repo = LogRepository(client)
        self.document_repo = DocumentRepo(client)

   async def ensure_schema(self):
        # self.client.insert_document(all_schema_classes, graph_type="schema")
        pass