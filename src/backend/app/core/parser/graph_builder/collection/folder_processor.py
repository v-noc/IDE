import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

from app.core.repository.structure.folder_repo import FolderRepo
from app.core.model.nodes import ProjectNode, FolderNode
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

    async def process_batch(
        self, change_set: ChangeSet, batch_size: int = 100
    ) -> List[FolderChange]:
        """
        Synchronize folder scopes using ID-first events from ChangeSet.
        """
        folder_changes: List[FolderChange] = []

        # Map absolute folder path -> stable folder id for all changed folders.
        # This allows parent resolution to avoid unnecessary DB lookups.
        path_to_id: Dict[str, str] = {
            tp.path: tp.id for tp in change_set.new_folders
        }
        path_to_id.update(
            {tp.path: tp.id for tp in change_set.modified_folders}
        )
        path_to_id.update({mv.new: mv.id for mv in change_set.moved_folders})

        # 1) Create only folders detector classified as new.
        await self._sync_tracked_folders_in_batches(
            folders=change_set.new_folders,
            mode="create",
            path_to_id=path_to_id,
            folder_changes=folder_changes,
            batch_size=batch_size,
        )
        # 2) Update only folders detector classified as modified.
        await self._sync_tracked_folders_in_batches(
            folders=change_set.modified_folders,
            mode="update",
            path_to_id=path_to_id,
            folder_changes=folder_changes,
            batch_size=batch_size,
        )
        # 3) Move only folders detector classified as moved.
        await self._move_folders_in_batches(
            moves=change_set.moved_folders,
            path_to_id=path_to_id,
            folder_changes=folder_changes,
            batch_size=batch_size,
        )

        # 2) Batch delete folders by stable id
        if change_set.deleted_folders:
            deleted_ids = [tp.id for tp in change_set.deleted_folders if tp.id]
            if deleted_ids:
                existing = await self.folder_repo.get_by_ids(deleted_ids, self.project_node.db_name)
                existing = {folder.id: folder for folder in existing}
                for node_id in deleted_ids:
                    node = existing.get(node_id)
                    if node:
                        folder_changes.append(FolderChange(
                            node=node, action="deleted"))
                        self._touched_folder_ids.add(node.id)
                await self.folder_repo.delete_batch(deleted_ids, self.project_node.db_name)

        return folder_changes

    async def _sync_tracked_folders_in_batches(
        self,
        *,
        folders: List[TrackedPath],
        mode: str,
        path_to_id: Dict[str, str],
        folder_changes: List[FolderChange],
        batch_size: int,
    ) -> None:
        if not folders:
            return

        for i in range(0, len(folders), batch_size):
            batch = folders[i: i + batch_size]
            await self._sync_tracked_folders_batch(
                batch=batch,
                mode=mode,
                path_to_id=path_to_id,
                folder_changes=folder_changes,
            )

    async def _move_folders_in_batches(
        self,
        *,
        moves: List[MoveEvent],
        path_to_id: Dict[str, str],
        folder_changes: List[FolderChange],
        batch_size: int,
    ) -> None:
        if not moves:
            return

        moved_folders = [TrackedPath(path=move.new, id=move.id)
                         for move in moves]
        for i in range(0, len(moved_folders), batch_size):
            batch = moved_folders[i: i + batch_size]
            await self._sync_tracked_folders_batch(
                batch=batch,
                mode="move",
                path_to_id=path_to_id,
                folder_changes=folder_changes,
            )

    async def _sync_tracked_folders_batch(
        self,
        *,
        batch: List[TrackedPath],
        mode: str,
        path_to_id: Dict[str, str],
        folder_changes: List[FolderChange],
    ) -> None:
        ids = [tp.id for tp in batch if tp.id]
        if not ids:
            return

        existing_by_id = await self.folder_repo.get_by_ids([id for id in ids], self.project_node.db_name)
        existing_by_id = {folder.id: folder for folder in existing_by_id}

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
                sorted(parent_qnames_needed), self.project_node.db_name
            )

        nodes_to_create: List[FolderNode] = []
        nodes_to_update: List[FolderNode] = []
        moves_to_execute: List[tuple[str, str, str]] = []

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
            is_create = mode == "create"
            is_move = mode == "move"

            if not node:
                node = FolderNode(
                    id=tp.id,
                    name=desired_name,
                    qname=desired_qname,
                    path=desired_path,
                    description=f"Folder {desired_name}",
                )
                nodes_to_create.append(node)
                if node.id not in self._touched_folder_ids:
                    folder_changes.append(
                        FolderChange(
                            node=node,
                            action="created" if not is_move else "updated",
                        )
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
                            FolderChange(
                                node=node,
                                action="created" if is_create else "updated",
                            )
                        )
                        self._touched_folder_ids.add(node.id)

            # Parent relationships only need to be set for newly created or moved folders.
            if is_create or is_move:

                parent_id = self.resolve_parent_id_for_abs_path(
                    abs_path=abs_path,
                    path_to_id=path_to_id,
                    parent_nodes_by_qname=parent_nodes_by_qname,
                )

                if parent_id:
                    moves_to_execute.append((tp.id, parent_id, "folder"))

        if nodes_to_create:
            await self.folder_repo.create(nodes_to_create, self.project_node.db_name)
        if nodes_to_update:
            await self.folder_repo.update_batch(nodes_to_update, self.project_node.db_name)
        if moves_to_execute:
            await self.folder_repo.move_batch(moves_to_execute, self.project_node.db_name)

    def qname_for_rel_path(self, rel_path: Path) -> str:
        parts = [p for p in rel_path.parts if p]
        if not parts:
            return self.project_node.name
        return ".".join([self.project_node.name] + parts)

    def resolve_parent_id_for_abs_path(
        self,
        *,
        abs_path: Path,
        path_to_id: Dict[str, str],
        parent_nodes_by_qname: Dict[str, FolderNode],
    ) -> Optional[str]:
        parent_abs = abs_path.parent
        if str(parent_abs) == str(self.project_path):
            # Always use self.project_node.id to ensure we use the persisted version
            return None

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
