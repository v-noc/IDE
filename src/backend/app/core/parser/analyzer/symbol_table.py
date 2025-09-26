from typing import List, Optional, Dict
from app.core.parser.analyzer.file_navigator import FileContainer
from app.core.parser.ast.models import BaseSchema
from app.core.parser.scope_manager.manager import ScopeManager
from app.models.node import ProjectNode


class SymbolTable:
    def __init__(self):
        self.project_node = Optional[ProjectNode]

        self.qname_to_node = Dict[str, BaseSchema]

        self.scope_manager: Optional[ScopeManager] = None

        self.file_containers: Dict[str, FileContainer] = {}

        self.unprocessed_files: List[str] = []
