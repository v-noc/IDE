from app.core.model.schemas import ensure_task_schema
from app.core.model.schemas.task_schema import BoardSchema
from app.core.model.tasks import BoardNode
from app.core.repository.base_repo import BaseRepo
from app.db.async_terminus_client import AsyncClient


class BoardRepo(BaseRepo[BoardNode, BoardSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, BoardNode, BoardSchema)

    async def ensure_schema(self) -> None:
        await ensure_task_schema(self.client)

    async def get_default(self) -> BoardNode | None:
        return await self.get_by_id("BoardSchema/default")
