from typing import List, Dict
from ..base.base_node_repo import BaseNodeRepository
from app.core.model.nodes import FunctionNode
from arangoasync.database import AsyncDatabase


class FunctionRepo(BaseNodeRepository[FunctionNode]):
    def __init__(self, db: AsyncDatabase):
        super().__init__(db, "nodes", FunctionNode)

