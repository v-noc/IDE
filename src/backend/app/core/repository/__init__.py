
from app.db.async_terminus_client import AsyncClient
from app.core.repository.code_elements.code_element_group import CodeElementGroupRepo
from app.core.repository.code_elements.call_group import CallGroupRepo
from app.core.repository.structure.structure_group import StructureGroupRepo


from .project_repo import ProjectRepo
from .structure.folder_repo import FolderRepo
from .structure.file_repo import FileRepo
from .code_elements.function_repo import FunctionRepo
from .code_elements.class_repo import ClassRepo
from .code_elements.call_repo import CallRepo
from .log_repo import LogRepository
from .document_repo import DocumentRepo
from .code_elements.code_element_repo import CodeElementRepo


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
        self.code_element_repo = CodeElementRepo(client)

        self.structure_group_repo = StructureGroupRepo(client)
        self.code_element_group_repo = CodeElementGroupRepo(client)
        self.call_group_repo = CallGroupRepo(client)
        self.log_repo = LogRepository(client)
        self.document_repo = DocumentRepo(client)
