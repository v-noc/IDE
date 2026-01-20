from typing import List, Dict
from ..base.base_node_repo import BaseNodeRepository
from app.core.model.nodes import ClassNode
from arangoasync.database import AsyncDatabase


class ClassRepo(BaseNodeRepository[ClassNode]):
    def __init__(self, db: AsyncDatabase):
        super().__init__(db, "nodes", ClassNode)

