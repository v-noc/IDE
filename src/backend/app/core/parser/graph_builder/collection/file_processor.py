import hashlib
import logging
from pathlib import Path
from typing import Dict, List

from app.core.model.nodes import ProjectNode, FileNode
from app.core.parser.graph_builder.collection.structure_batch import StructureBatchPlan
from app.core.parser.graph_builder.discovery.change_detector import (
    ChangeSet,
    MoveEvent,
    TrackedPath,
)
from app.core.parser.graph_builder.discovery.scanner import ScanResult

logger = logging.getLogger(__name__)


class FileProcessor:
    """
    Prepares file structure operations from ChangeSet. No DB calls.
    Returns StructureBatchPlan (insert/update/delete/move) for batch flush.
    """

    def __init__(self, project_node: ProjectNode):
        self.project_node = project_node
        self.project_path = Path(project_node.path)

    def prepare_batch(
        self,
        change_set: ChangeSet,
        scan_result: ScanResult,
    ) -> StructureBatchPlan:
        """
        Build insert/update/delete/move lists from ChangeSet. No API calls.
        """
        plan = StructureBatchPlan()

        folder_path_to_id: Dict[str, str] = {
            tp.path: tp.id for tp in change_set.new_folders
        }
        folder_path_to_id.update(
            {tp.path: tp.id for tp in change_set.modified_folders}
        )
        folder_path_to_id.update(
            {mv.new_path: mv.id for mv in change_set.moved_folders}
        )

        for tp in change_set.new_files:
            self._add_file_create(tp, scan_result, plan)

        for tp in change_set.modified_files:
            self._add_file_update(tp, scan_result, plan)

        for move in change_set.moved_files:
            parent_id = move.new_parent_id
            tp = TrackedPath(path=move.new_path, id=move.id,
                             parent_id=parent_id)
            self._add_file_move(tp, scan_result, plan)

        for tp in change_set.deleted_files:
            if tp.id:
                plan.delete.append(tp.id)

        return plan

    def _add_file_create(
        self,
        tp: TrackedPath,
        scan_result: ScanResult,
        plan: StructureBatchPlan,
    ) -> None:
        if not tp.id:
            return
        node = self._file_node_from_tracked(tp, scan_result)
        if not node:
            return
        plan.insert.append(node)
        if tp.parent_id:
            plan.move.append((tp.id, tp.parent_id, "file"))

    def _add_file_update(
        self,
        tp: TrackedPath,
        scan_result: ScanResult,
        plan: StructureBatchPlan,
    ) -> None:
        if not tp.id:
            return
        node = self._file_node_from_tracked(tp, scan_result)
        if not node:
            return
        plan.update.append(node)

    def _add_file_move(
        self,
        tp: TrackedPath,
        scan_result: ScanResult,
        plan: StructureBatchPlan,
    ) -> None:
        if not tp.id:
            return
        node = self._file_node_from_tracked(tp, scan_result)
        if not node:
            return
        plan.update.append(node)
        if tp.parent_id:
            plan.move.append((tp.id, tp.parent_id, "file"))

    def _file_node_from_tracked(
        self,
        tp: TrackedPath,
        scan_result: ScanResult,
    ) -> FileNode | None:
        abs_path = Path(tp.path)
        try:
            rel_path = abs_path.relative_to(self.project_path)
        except ValueError:
            logger.warning(
                "File %s is not inside project path %s; skipping",
                tp.path,
                self.project_path,
            )
            return None
        name = abs_path.stem
        qname = self.qname_for_rel_path(rel_path, is_file=True)
        checksum = self._resolve_checksum(tp.path, abs_path, scan_result)
        return FileNode(
            id=tp.id,
            name=name,
            qname=qname,
            path=str(abs_path),
            hash=checksum,
            description=f"File {name}",
        )

    def qname_for_rel_path(self, rel_path: Path, is_file: bool = False) -> str:
        parts = [p for p in rel_path.parts if p]
        if not parts:
            return self.project_node.name

        if is_file:
            q_parts = [self.project_node.name]
            for idx, part in enumerate(parts):
                is_last = idx == len(parts) - 1
                name = Path(part).stem if (is_last and is_file) else part
                q_parts.append(name)
            return ".".join(q_parts)

        return ".".join([self.project_node.name] + parts)

    def _calculate_checksum(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _resolve_checksum(
        self,
        file_path: str,
        abs_path: Path,
        scan_result: ScanResult,
    ) -> str:
        return scan_result.files.get(file_path) or self._calculate_checksum(abs_path)
