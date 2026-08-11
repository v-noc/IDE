
from app.db.async_terminus_client import AsyncClient
from app.core.repository.code_elements.code_element_group import (
    CodeElementGroupRepo,
)
from app.core.repository.code_elements.call_group import CallGroupRepo
from app.core.repository.structure.structure_group import StructureGroupRepo


from .project_repo import ProjectRepo
from .structure.structure_repo import StructureRepo
from .code_elements.call_repo import CallRepo
from .log_repo import LogRepository
from .document_repo import DocumentRepo
from .code_elements.code_element_repo import CodeElementRepo
from .code_elements.test_repo import TestRepo
from .code_elements.play_ground_repo import PlayGroundRepo
from .container_repo import ContainerRepo
from .conversation_repo import ConversationRepo
from .task_repo import TaskRepo
from .board_repo import BoardRepo


class Repositories:
    """A container for all repository instances."""

    def __init__(self, client: AsyncClient):
        # Generic Node Repo for mixed-type queries
        self.client = client

        # Specific Node Repos for type-specific operations
        self.project_repo = ProjectRepo(client)
        self.structure_repo = StructureRepo(client)
        self.call_repo = CallRepo(client)
        self.code_element_repo = CodeElementRepo(client)

        self.structure_group_repo = StructureGroupRepo(client)
        self.code_element_group_repo = CodeElementGroupRepo(client)
        self.call_group_repo = CallGroupRepo(client)
        self.log_repo = LogRepository(client)
        self.document_repo = DocumentRepo(client)
        self.test_repo = TestRepo(client)
        self.play_ground_repo = PlayGroundRepo(client)

        self.container_repo = ContainerRepo(client)
        self.conversation_repo = ConversationRepo(client)
        self.task_repo = TaskRepo(client)
        self.board_repo = BoardRepo(client)
