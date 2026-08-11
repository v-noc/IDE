from app.core.model.schemas import ensure_task_schema
from app.core.model.schemas.task_schema import TaskSchema
from app.core.model.tasks import TaskNode
from app.core.repository.base_repo import BaseRepo
from app.db.async_terminus_client import AsyncClient


class TaskRepo(BaseRepo[TaskNode, TaskSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, TaskNode, TaskSchema)

    async def ensure_schema(self) -> None:
        await ensure_task_schema(self.client)
