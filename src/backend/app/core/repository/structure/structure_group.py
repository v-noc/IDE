from app.core.repository.base_repo import BaseRepo
from app.db.async_terminus_client import AsyncClient
from app.core.model.nodes import StructureGroupNode
from app.core.model.schemas import StructureGroupSchema


class StructureGroupRepo(BaseRepo[StructureGroupNode, StructureGroupSchema]):
    def __init__(self, client: AsyncClient):
        self.client = client
