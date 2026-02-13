# from .base.base_node_repo import BaseNodeRepository
# from app.core.model.nodes import GroupNode
# from arangoasync.database import AsyncDatabase


# class GroupRepo(BaseNodeRepository[GroupNode]):
#     def __init__(self, db: AsyncDatabase):
#         super().__init__(db, "nodes", GroupNode)

from app.db.async_terminus_client import AsyncClient


class GroupRepo():
    def __init__(self, client: AsyncClient):
        self.client = client

    def get_group_by_id(self, group_id: str):
        pass

    def get_group_by_filed(self, field_name: str, field_value: str):
        pass
