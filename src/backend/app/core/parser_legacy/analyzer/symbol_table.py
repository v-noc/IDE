from typing import List, Optional, Dict, Set
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

        repos = Repositories(db)
        self.node_service = {
            "project": ProjectService(repos),
            "folder": FolderService(repos),
            "file": FileService(repos),
            "class": ClassService(repos),
            "function": FunctionService(repos),
            "call": CallService(repos),
        }

        # Tracks expected direct call relationships during analysis.
        # Mapping: parent_id -> set of target_ids
        self.parent_id_to_seen_call_targets: Dict[str, Set[str]] = {}

    def register_direct_call(self, parent_id: str, target_id: str) -> None:
        """Register a direct call from parent to target for this analysis.

        Collected by the call handler and later used to prune stale
        call children.
        """
        if not parent_id or not target_id:
            return
        bucket = self.parent_id_to_seen_call_targets.setdefault(
            parent_id, set())
        bucket.add(target_id)

    def prune_stale_direct_calls(self, container_id: str) -> None:
        """Remove direct call children under container that are not seen.

        - Looks up expected targets recorded for container_id during analysis
        - Fetches immediate call children via contains_edges
        - For each call child, resolves its target; deletes if not expected
        - Clears the recorded expectations for container_id afterwards
        """
        try:
            expected_targets = self.parent_id_to_seen_call_targets.get(
                container_id, set()
            )
            # Resolve the container node to determine proper repo
            container_node = (
                self.node_service["project"].repos.nodes.get_by_id(
                    container_id
                )
            )
            if not container_node:
                # Nothing to prune
                return

            node_type = getattr(container_node, "node_type", None)
            if node_type not in ("file", "class", "function", "call"):
                return

            # Choose correct repository for containment traversal
            if node_type == "file":
                repo = self.node_service["file"].repos.file_repo
            elif node_type == "class":
                repo = self.node_service["class"].repos.class_repo
            elif node_type == "function":
                repo = self.node_service["function"].repos.function_repo
            else:
                repo = self.node_service["call"].repos.call_repo

            children = repo.get_containment_tree(
                container_id, depth=1
            ) or []

            # Identify stale call children
            stale_call_keys: List[str] = []
            for item in children:
                vertex = item.get("vertex") or {}
                parent_id = item.get("parent_id")
                if parent_id != container_id:
                    continue  # only immediate
                if vertex.get("node_type") != "call":
                    continue
                call_id = vertex.get("_id")
                call_key = vertex.get("_key")
                if not call_id or not call_key:
                    continue

                # Resolve call's target
                target = self.node_service["call"].repos.call_repo.get_target(
                    call_id
                )
                target_id = getattr(target, "id", None) if target else None

                # If this target isn't expected, mark for deletion
                if not target_id or target_id not in expected_targets:
                    stale_call_keys.append(call_key)

            for key in stale_call_keys:
                try:
                    self.node_service["call"].delete(key)
                except Exception:
                    # Best-effort pruning; ignore failures
                    continue
        finally:
            # Clear expectations for this container
            self.parent_id_to_seen_call_targets.pop(container_id, None)

    def prune_all_recorded_calls(self) -> None:
        """Prune stale direct calls for all recorded parents.

        Iterates over every parent_id that registered expected call targets
        during this analysis pass and prunes its immediate call children.
        """
        # Copy keys to avoid mutation during iteration
        parent_ids = list(self.parent_id_to_seen_call_targets.keys())
        for parent_id in parent_ids:
            self.prune_stale_direct_calls(parent_id)
