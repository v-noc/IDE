import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Set

from app.core.repository.folder_repo import FolderRepo
from app.core.model.nodes import ProjectNode, FolderNode
from app.core.parser.graph_builder.discovery.change_detector import (
    ChangeSet,
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
    Handles folder hierarchy synchronization using ID-first optimization.
    Replaces the legacy recursive HierarchyBuilder for folders.
    """

    def __init__(self, project_node: ProjectNode, folder_repo: FolderRepo):
        self.project_node = project_node
        self.project_path = Path(project_node.path)
        self.folder_repo = folder_repo
        self._touched_folder_ids: Set[str] = set()

    def reset_session(self) -> None:
        """Reset cached folder touches for a new orchestration run."""
        self._touched_folder_ids.clear()

    async def ensure_folder(
        self, rel_path: Path
    ) -> Optional[FolderBuildResult]:
        """
        Ensure that a folder hierarchy exists for the given relative path.
        """
        rel_parts = [part for part in rel_path.parts if part]
        folder_changes: List[FolderChange] = []

        root = self.project_node

        if not rel_parts:
            return FolderBuildResult(node=root, folder_changes=folder_changes)

        current_qname = self.project_node.name
        qnames_to_check = []
        qname_paths = {}

        for idx, part in enumerate(rel_parts):
            current_qname = f"{current_qname}.{part}"
            path_so_far = self.project_path / Path(*rel_parts[: idx + 1])
            qnames_to_check.append(current_qname)
            qname_paths[current_qname] = (part, str(path_so_far))

        existing_nodes = await self.folder_repo.get_by_qnames(qnames_to_check)

        nodes_to_create = []
        moves_to_execute = []  # List of (child_id, parent_id)
        current_parent = root

        for qname in qnames_to_check:
            node = existing_nodes.get(qname)
            display_name, path_so_far = qname_paths[qname]

            if not node:
                node = FolderNode(
                    key=str(uuid.uuid4()),
                    name=display_name,
                    qname=qname,
                    path=path_so_far,
                    description=f"Folder {display_name}",
                    node_type="folder"
                )
                nodes_to_create.append(node)
                moves_to_execute.append((node.id, current_parent.id))

                folder_changes.append(FolderChange(
                    node=node, action="created"))
                self._touched_folder_ids.add(node.id)

            current_parent = node

        if nodes_to_create:
            await self.folder_repo.create_batch(nodes_to_create)
        if moves_to_execute:
            await self.folder_repo.move_batch(moves_to_execute)

        return FolderBuildResult(
            node=current_parent, folder_changes=folder_changes
        )

    async def process_batch(
        self, change_set: ChangeSet, batch_size: int = 100
    ) -> List[FolderChange]:
        """
        Synchronize folder scopes using ID-first events from ChangeSet.
        """
        folder_changes: List[FolderChange] = []

        # Ensure project root scope exists
        root = self.project_node

        # Map absolute folder path -> stable folder id for any changed folders
        path_to_id: Dict[str, str] = {
            tp.path: tp.id for tp in change_set.new_folders}
        path_to_id.update({mv.new: mv.id for mv in change_set.moved_folders})

        # 1) Upsert moved folders (treated as updates) and newly-created folders
        moved_tracked = [
            TrackedPath(path=mv.new, id=mv.id)
            for mv in change_set.moved_folders
        ]
        new_tracked = list(change_set.new_folders)

        await self._upsert_folders_in_batches(
            folders=moved_tracked,
            root_node=root,
            path_to_id=path_to_id,
            folder_changes=folder_changes,
            default_action="updated",
            batch_size=batch_size,
        )
        await self._upsert_folders_in_batches(
            folders=new_tracked,
            root_node=root,
            path_to_id=path_to_id,
            folder_changes=folder_changes,
            default_action="created",
            batch_size=batch_size,
        )

        # 2) Batch delete folders by stable id
        if change_set.deleted_folders:
            deleted_ids = [tp.id for tp in change_set.deleted_folders if tp.id]
            if deleted_ids:
                existing = await self.folder_repo.get_by_ids(deleted_ids)
                for node_id in deleted_ids:
                    node = existing.get(node_id)
                    if node:
                        folder_changes.append(FolderChange(
                            node=node, action="deleted"))
                        self._touched_folder_ids.add(node.id)
                await self.folder_repo.delete_batch(deleted_ids)

        return folder_changes

    async def _upsert_folders_in_batches(
        self,
        *,
        folders: List[TrackedPath],
        root_node: FolderNode,
        path_to_id: Dict[str, str],
        folder_changes: List[FolderChange],
        default_action: str,
        batch_size: int,
    ) -> None:
        if not folders:
            return

        for i in range(0, len(folders), batch_size):
            batch = folders[i: i + batch_size]
            await self._upsert_folders_batch(
                batch=batch,
                root_node=root_node,
                path_to_id=path_to_id,
                folder_changes=folder_changes,
                default_action=default_action,
            )

    async def _upsert_folders_batch(
        self,
        *,
        batch: List[TrackedPath],
        root_node: FolderNode,
        path_to_id: Dict[str, str],
        folder_changes: List[FolderChange],
        default_action: str,
    ) -> None:
        ids = [tp.id for tp in batch if tp.id]
        if not ids:
            return

        existing_by_id = await self.folder_repo.get_by_ids(ids)

        # Pre-fetch any parent scopes not present in the current change mapping.
        parent_qnames_needed: Set[str] = set()
        for tp in batch:
            parent_abs = str(Path(tp.path).parent)
            if parent_abs == str(self.project_path):
                continue
            if parent_abs in path_to_id:
                continue
            try:
                rel_p = Path(parent_abs).relative_to(self.project_path)
            except ValueError:
                continue
            parent_qnames_needed.add(self.qname_for_rel_path(rel_p))

        parent_nodes_by_qname: Dict[str, FolderNode] = {}
        if parent_qnames_needed:
            parent_nodes_by_qname = await self.folder_repo.get_by_qnames(
                sorted(parent_qnames_needed)
            )

        nodes_to_create: List[FolderNode] = []
        nodes_to_update: List[FolderNode] = []
        moves_to_execute: List[tuple[str, str]] = []

        for tp in batch:
            if not tp.id:
                continue

            abs_path = Path(tp.path)
            try:
                rel_path = abs_path.relative_to(self.project_path)
            except ValueError:
                logger.warning(
                    "Folder %s is not inside project path %s; skipping",
                    tp.path,
                    self.project_path,
                )
                continue

            desired_name = abs_path.name
            desired_qname = self.qname_for_rel_path(rel_path)
            desired_path = str(abs_path)

            node = existing_by_id.get(tp.id)
            if not node:
                node = FolderNode(
                    key=tp.id,
                    name=desired_name,
                    qname=desired_qname,
                    path=desired_path,
                    description=f"Folder {desired_name}",
                    node_type="folder"
                )
                nodes_to_create.append(node)
                if node.id not in self._touched_folder_ids:
                    folder_changes.append(
                        FolderChange(node=node, action=default_action)
                    )
                    self._touched_folder_ids.add(node.id)
            else:
                # Only update if relevant properties changed
                changed = (
                    node.name != desired_name
                    or node.qname != desired_qname
                    or node.path != desired_path
                )
                if changed:
                    node.name = desired_name
                    node.qname = desired_qname
                    node.path = desired_path
                    nodes_to_update.append(node)
                    if node.id not in self._touched_folder_ids:
                        folder_changes.append(
                            FolderChange(node=node, action="updated")
                        )
                        self._touched_folder_ids.add(node.id)

            # Relink parent-child relationship
            parent_id = self.resolve_parent_id_for_abs_path(
                abs_path=abs_path,
                root_node=root_node,
                path_to_id=path_to_id,
                parent_nodes_by_qname=parent_nodes_by_qname,
            )
            if parent_id:
                moves_to_execute.append((tp.id, parent_id))

        if nodes_to_create:
            await self.folder_repo.create_batch(nodes_to_create)
        if nodes_to_update:
            await self.folder_repo.update_batch(nodes_to_update)
        if moves_to_execute:
            await self.folder_repo.move_batch(moves_to_execute)

    def qname_for_rel_path(self, rel_path: Path) -> str:
        parts = [p for p in rel_path.parts if p]
        if not parts:
            return self.project_node.name
        return ".".join([self.project_node.name] + parts)

    def resolve_parent_id_for_abs_path(
        self,
        *,
        abs_path: Path,
        root_node: FolderNode,
        path_to_id: Dict[str, str],
        parent_nodes_by_qname: Dict[str, FolderNode],
    ) -> Optional[str]:
        parent_abs = abs_path.parent
        if str(parent_abs) == str(self.project_path):
            return root_node.id

        parent_id = path_to_id.get(str(parent_abs))
        if parent_id:
            return parent_id

        try:
            rel_parent = parent_abs.relative_to(self.project_path)
        except ValueError:
            return None

        parent_qname = self.qname_for_rel_path(rel_parent)
        parent_node = parent_nodes_by_qname.get(parent_qname)
        return parent_node.id if parent_node else None
