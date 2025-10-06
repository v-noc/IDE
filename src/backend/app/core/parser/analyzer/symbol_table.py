from typing import List, Optional, Dict
from app.core.parser.analyzer.file_navigator import FileContainer
from app.core.parser.scope_manager.manager import ScopeManager

from app.core.services import (
    ProjectService,
    FolderService,
    FileService,
    ClassService,
    FunctionService,
    CallService,
)
from app.core.repository import Repositories
from arango.database import StandardDatabase

from app.core.model.base import BaseNode
from app.core.parser.ast.models import FunctionSchema
from app.core.model.nodes import CallNode, ProjectNode


class SymbolTable:
    def __init__(self, db: StandardDatabase):
        self.project_node: Optional[ProjectNode] = None
        self.qname_to_node: Dict[str, BaseNode] = {}
        self.scope_manager: Optional[ScopeManager] = None

        self.file_containers: Dict[str, FileContainer] = {}

        self.unprocessed_files: List[str] = []

        self.call_node_stack: List[CallNode] = []

        self.qname_to_function_node: Dict[str, FunctionSchema] = {}

        # Track how many lines we've inserted per file when writing comments,
        # so later writes can adjust line numbers accordingly.
        self.file_path_to_line_inserts: Dict[str, int] = {}

        repos = Repositories(db)
        self.node_service = {
            "project": ProjectService(repos),
            "folder": FolderService(repos),
            "file": FileService(repos),
            "class": ClassService(repos),
            "function": FunctionService(repos),
            "call": CallService(repos),
        }
