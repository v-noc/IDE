import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from app.core.model.nodes import ProjectNode, FolderNode
from app.core.parser.graph_builder.collection.structure_batch import StructureBatchPlan
from app.core.parser.graph_builder.discovery.change_detector import (
    ChangeSet,
    MoveEvent,
    TrackedPath,
)

logger = logging.getLogger(__name__)


@dataclass
class FolderChange:
    node: FolderNode
    action: str  # "created", "updated", or "deleted"


@dataclass
class FolderBuildResult:
    node: FolderNode
    folder_changes: List[FolderChange]


class FolderProcessor:
    """
    Prepares folder structure operations from ChangeSet. No DB calls.
    Returns StructureBatchPlan (insert/update/delete/move) for batch flush.
    """

    def __init__(self, project_node: ProjectNode):
        self.project_node = project_node
        self.project_path = Path(project_node.path)

    def reset_session(self) -> None:
        """Reset cached state for a new orchestration run."""
        pass

    def prepare_batch(self, change_set: ChangeSet) -> StructureBatchPlan:
        """
        Build insert/update/delete/move lists from ChangeSet. No API calls.
        """
        plan = StructureBatchPlan()

        path_to_id: Dict[str, str] = {
            tp.path: tp.id for tp in change_set.new_folders
        }
        path_to_id.update(
            {tp.path: tp.id for tp in change_set.modified_folders})
        path_to_id.update(
            {mv.new_path: mv.id for mv in change_set.moved_folders})

        for tp in change_set.new_folders:
            self._add_folder_create(tp, plan)

        for tp in change_set.modified_folders:
            self._add_folder_update(tp, plan)

        for move in change_set.moved_folders:
            parent_id = move.new_parent_id
            tp = TrackedPath(path=move.new_path, id=move.id,
                             parent_id=parent_id)

            self._add_folder_move(tp, plan)

        for tp in change_set.deleted_folders:
            if tp.id:
                plan.delete.append(tp.id)

        return plan

    def _add_folder_create(self, tp: TrackedPath, plan: StructureBatchPlan) -> None:
        if not tp.id:
            return
        node = self._folder_node_from_tracked(tp)
        if not node:
            return
        plan.insert.append(node)
        if tp.parent_id:
            plan.move.append((tp.id, tp.parent_id, "folder"))

    def _add_folder_update(self, tp: TrackedPath, plan: StructureBatchPlan) -> None:
        if not tp.id:
            return
        node = self._folder_node_from_tracked(tp)
        if not node:
            return
        plan.update.append(node)

    def _add_folder_move(self, tp: TrackedPath, plan: StructureBatchPlan) -> None:
        if not tp.id:
            return
        node = self._folder_node_from_tracked(tp)
        if not node:
            return
        plan.update.append(node)
        if tp.parent_id:
            plan.move.append((tp.id, tp.parent_id, "folder"))

    def _folder_node_from_tracked(self, tp: TrackedPath) -> FolderNode | None:
        abs_path = Path(tp.path)
        try:
            rel_path = abs_path.relative_to(self.project_path)
        except ValueError:
            logger.warning(
                "Folder %s is not inside project path %s; skipping",
                tp.path,
                self.project_path,
            )
            return None
        name = abs_path.name
        qname = self.qname_for_rel_path(rel_path)
        return FolderNode(
            id=tp.id,
            name=name,
            qname=qname,
            path=str(abs_path),
            description=f"Folder {name}",
        )

    def qname_for_rel_path(self, rel_path: Path) -> str:
        parts = [p for p in rel_path.parts if p]
        if not parts:
            return self.project_node.name
        return ".".join([self.project_node.name] + parts)
