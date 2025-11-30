import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel, ScopeType
from app.core.model.nodes import ProjectNode

logger = logging.getLogger(__name__)


@dataclass
class FolderChange:
    scope: ScopeModel
    action: str  # "created", "updated", or "deleted"


@dataclass
class HierarchyBuildResult:
    scope: ScopeModel
    folder_changes: List[FolderChange]


class HierarchyBuilder:
    def __init__(self, project_node: ProjectNode, scope_manager: ScopeManager):
        self.project_node = project_node
        self.project_path = Path(project_node.path)
        self.manager = scope_manager
        self._touched_folder_ids: set[str] = set()

    def reset_session(self) -> None:
        """Reset cached folder touches for a new orchestration run."""
        self._touched_folder_ids.clear()

    def build_hierarchy(self, rel_path: Path, checksum: str) -> Optional[HierarchyBuildResult]:
        """
        Build folder + file hierarchy for a file path.
        Returns the resulting file scope and folder change metadata.
        """
        return self._ensure_path(rel_path, checksum=checksum, terminal_type=ScopeType.FILE)

    def ensure_folder(self, rel_path: Path) -> Optional[HierarchyBuildResult]:
        """
        Ensure that a folder hierarchy exists for the given relative path.
        """
        return self._ensure_path(rel_path, checksum=None, terminal_type=ScopeType.FOLDER)

    def _ensure_path(
        self,
        rel_path: Path,
        checksum: Optional[str],
        terminal_type: ScopeType,
    ) -> Optional[HierarchyBuildResult]:
        rel_parts = [part for part in rel_path.parts if part]
        folder_changes: List[FolderChange] = []
        root = self._ensure_root(folder_changes)
        folder_chain = [{"scope": root, "parent": None}]

        if not rel_parts and terminal_type == ScopeType.FOLDER:
            return HierarchyBuildResult(scope=root, folder_changes=folder_changes)

        current_parent = root
        current_qname = self.project_node.name
        file_scope: Optional[ScopeModel] = None
        hierarchy_changed = False

        for idx, part in enumerate(rel_parts):
            is_last = idx == len(rel_parts) - 1
            is_file_node = terminal_type == ScopeType.FILE and is_last
            display_name = Path(part).stem if is_file_node else part
            current_qname = f"{current_qname}.{display_name}"
            scope = self.manager.get_scope_by_qname(current_qname)
            path_so_far = self.project_path / Path(*rel_parts[: idx + 1])

            if not scope:
                scope_type = ScopeType.FILE if is_file_node else ScopeType.FOLDER
                scope = self.manager.create_scope(
                    name=display_name,
                    qname=current_qname,
                    scope_type=scope_type,
                    file_path=str(path_so_far),
                    start_line=0,
                    start_col=0,
                    end_line=0,
                    end_col=0,
                    checksum=checksum if is_file_node else None,
                )
                if current_parent:
                    self.manager.link_parent_child(current_parent.id, scope.id)
                if scope_type == ScopeType.FOLDER:
                    folder_changes.append(FolderChange(
                        scope=scope, action="created"))
                    self._touched_folder_ids.add(scope.id)
                    folder_chain.append(
                        {"scope": scope, "parent": current_parent})
                else:
                    file_scope = scope
                hierarchy_changed = True
            else:
                if is_file_node:
                    file_scope = scope
                    checksum_changed = checksum is not None and scope.checksum != checksum
                    if checksum_changed:
                        scope.checksum = checksum
                        scope = self.manager.update_scope(scope)
                        hierarchy_changed = True
                else:
                    folder_chain.append(
                        {"scope": scope, "parent": current_parent})

            current_parent = scope

        if not file_scope and terminal_type == ScopeType.FILE:
            logger.error("Failed to build hierarchy for %s", rel_path)
            return None

        if hierarchy_changed:
            skip_last = terminal_type == ScopeType.FOLDER
            self._bubble_folder_chain(
                folder_chain, folder_changes, skip_last=skip_last)

        terminal_scope = file_scope if terminal_type == ScopeType.FILE else folder_chain[-1]["scope"]
        return HierarchyBuildResult(scope=terminal_scope, folder_changes=folder_changes)

    def _ensure_root(self, folder_changes: List[FolderChange]) -> ScopeModel:
        current_qname = self.project_node.name
        root = self.manager.get_scope_by_qname(current_qname)
        if root:
            return root

        root = self.manager.create_scope(
            name=self.project_node.name,
            qname=current_qname,
            scope_type=ScopeType.FOLDER,
            scope_id=self.project_node.id,
            file_path=str(self.project_path),
            start_line=0,
            start_col=0,
            end_line=0,
            end_col=0,
        )
        folder_changes.append(FolderChange(scope=root, action="created"))
        self._touched_folder_ids.add(root.id)
        return root

    def _bubble_folder_chain(
        self,
        folder_chain: List[dict],
        folder_changes: List[FolderChange],
        skip_last: bool = False,
    ) -> None:
        chain = folder_chain[:-1] if skip_last else folder_chain
        for entry in reversed(chain):
            scope = entry["scope"]
            parent = entry["parent"]
            if not scope or scope.id in self._touched_folder_ids:
                continue
            folder_changes.append(FolderChange(scope=scope, action="updated"))
            self._touched_folder_ids.add(scope.id)
