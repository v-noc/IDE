import logging
import uuid
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Iterable

from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel, ScopeType
from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.discovery.change_detector import (
    ChangeSet,
    TrackedPath,
    MoveEvent,
)

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

    async def build_hierarchy(
        self, rel_path: Path, checksum: str
    ) -> Optional[HierarchyBuildResult]:
        """
        Build folder + file hierarchy for a file path.
        Returns the resulting file scope and folder change metadata.
        """
        return await self._ensure_path(
            rel_path, checksum=checksum, terminal_type=ScopeType.FILE
        )

    async def ensure_folder(
        self, rel_path: Path
    ) -> Optional[HierarchyBuildResult]:
        """
        Ensure that a folder hierarchy exists for the given relative path.
        """
        return await self._ensure_path(
            rel_path, checksum=None, terminal_type=ScopeType.FOLDER
        )

    async def process_folder_changes_batch(
        self, change_set: ChangeSet, batch_size: int = 100
    ) -> List[FolderChange]:
        """
        Synchronize folder scopes using ID-first events from ChangeSet.

        - Moves: update folder scope properties by stable id + relink parent
        - New: upsert (create/update) folder scopes by stable id + relink parent
        - Deleted: batch delete folder scopes by stable id
        """
        folder_changes: List[FolderChange] = []

        # Ensure project root scope exists
        root = await self._ensure_root(folder_changes)

        # Map absolute folder path -> stable folder id for any changed folders
        path_to_id: Dict[str, str] = {
            tp.path: tp.id for tp in change_set.new_folders}
        path_to_id.update({mv.new: mv.id for mv in change_set.moved_folders})

        # 1) Upsert moved folders (treated as updates) and newly-created folders
        moved_tracked = [TrackedPath(path=mv.new, id=mv.id)
                         for mv in change_set.moved_folders]
        new_tracked = list(change_set.new_folders)

        await self._upsert_folders_in_batches(
            folders=moved_tracked,
            root_scope=root,
            path_to_id=path_to_id,
            folder_changes=folder_changes,
            default_action="updated",
            batch_size=batch_size,
        )
        await self._upsert_folders_in_batches(
            folders=new_tracked,
            root_scope=root,
            path_to_id=path_to_id,
            folder_changes=folder_changes,
            default_action="created",
            batch_size=batch_size,
        )

        # 2) Batch delete folders by stable id
        if change_set.deleted_folders:
            deleted_ids = [tp.id for tp in change_set.deleted_folders if tp.id]
            if deleted_ids:
                existing = await self.manager.batch_get_scopes_by_ids(deleted_ids)
                for scope_id in deleted_ids:
                    scope = existing.get(scope_id)
                    if scope and scope.type == ScopeType.FOLDER:
                        folder_changes.append(FolderChange(
                            scope=scope, action="deleted"))
                        self._touched_folder_ids.add(scope.id)
                await self.manager.batch_delete_scopes(deleted_ids)

        return folder_changes

    async def _upsert_folders_in_batches(
        self,
        *,
        folders: List[TrackedPath],
        root_scope: ScopeModel,
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
                root_scope=root_scope,
                path_to_id=path_to_id,
                folder_changes=folder_changes,
                default_action=default_action,
            )

    async def _upsert_folders_batch(
        self,
        *,
        batch: List[TrackedPath],
        root_scope: ScopeModel,
        path_to_id: Dict[str, str],
        folder_changes: List[FolderChange],
        default_action: str,
    ) -> None:
        ids = [tp.id for tp in batch if tp.id]
        if not ids:
            return

        existing_by_id = await self.manager.batch_get_scopes_by_ids(ids)

        # Pre-fetch any parent scopes not present in the current change mapping.
        parent_qnames_needed: set[str] = set()
        for tp in batch:
            parent_abs = str(Path(tp.path).parent)
            if parent_abs == str(self.project_path):
                continue
            if parent_abs in path_to_id:
                continue
            try:
                rel_parent = Path(parent_abs).relative_to(self.project_path)
            except ValueError:
                continue
            parent_qnames_needed.add(self._qname_for_folder_rel(rel_parent))

        parent_scopes_by_qname: Dict[str, ScopeModel] = {}
        if parent_qnames_needed:
            parent_scopes_by_qname = await self.manager.batch_get_scopes_by_qnames(
                sorted(parent_qnames_needed)
            )

        scopes_to_create: List[ScopeModel] = []
        scopes_to_update: List[ScopeModel] = []
        relationships_to_relink: List[dict[str, str]] = []

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
            desired_qname = self._qname_for_folder_rel(rel_path)
            desired_file_path = str(abs_path)

            scope = existing_by_id.get(tp.id)
            if not scope:
                scope = ScopeModel(
                    id=tp.id,
                    name=desired_name,
                    qname=desired_qname,
                    type=ScopeType.FOLDER,
                    file_path=desired_file_path,
                    start_line=0,
                    start_col=0,
                    end_line=0,
                    end_col=0,
                    checksum=None,
                )
                scopes_to_create.append(scope)
                if scope.id not in self._touched_folder_ids:
                    folder_changes.append(
                        FolderChange(scope=scope, action=default_action)
                    )
                    self._touched_folder_ids.add(scope.id)
            else:
                # Only update if relevant properties changed
                changed = (
                    scope.name != desired_name
                    or scope.qname != desired_qname
                    or scope.file_path != desired_file_path
                )
                if changed:
                    scope.name = desired_name
                    scope.qname = desired_qname
                    scope.file_path = desired_file_path
                    scopes_to_update.append(scope)
                    if scope.id not in self._touched_folder_ids:
                        folder_changes.append(
                            FolderChange(scope=scope, action="updated")
                        )
                        self._touched_folder_ids.add(scope.id)

            # Relink parent-child relationship based on filesystem structure
            parent_id = self._resolve_parent_id_for_abs_path(
                abs_path=abs_path,
                root_scope=root_scope,
                path_to_id=path_to_id,
                parent_scopes_by_qname=parent_scopes_by_qname,
            )
            if parent_id:
                relationships_to_relink.append(
                    {"parent_id": parent_id, "child_id": tp.id}
                )

        if scopes_to_create:
            await self.manager.batch_create_scopes(scopes_to_create)
        if scopes_to_update:
            await self.manager.batch_update_scopes(scopes_to_update)
        if relationships_to_relink:
            await self.manager.batch_relink_parent_child(relationships_to_relink)

    def _qname_for_folder_rel(self, rel_path: Path) -> str:
        parts = [p for p in rel_path.parts if p]
        if not parts:
            return self.project_node.name
        return ".".join([self.project_node.name] + parts)

    def _resolve_parent_id_for_abs_path(
        self,
        *,
        abs_path: Path,
        root_scope: ScopeModel,
        path_to_id: Dict[str, str],
        parent_scopes_by_qname: Dict[str, ScopeModel],
    ) -> Optional[str]:
        parent_abs = abs_path.parent
        if str(parent_abs) == str(self.project_path):
            return root_scope.id

        parent_id = path_to_id.get(str(parent_abs))
        if parent_id:
            return parent_id

        try:
            rel_parent = parent_abs.relative_to(self.project_path)
        except ValueError:
            return None

        parent_qname = self._qname_for_folder_rel(rel_parent)
        parent_scope = parent_scopes_by_qname.get(parent_qname)
        return parent_scope.id if parent_scope else None

    async def _ensure_path(
        self,
        rel_path: Path,
        checksum: Optional[str],
        terminal_type: ScopeType,
    ) -> Optional[HierarchyBuildResult]:
        rel_parts = [part for part in rel_path.parts if part]
        folder_changes: List[FolderChange] = []

        root = await self._ensure_root(folder_changes)
        folder_chain = [{"scope": root, "parent": None}]

        if not rel_parts and terminal_type == ScopeType.FOLDER:
            return HierarchyBuildResult(
                scope=root, folder_changes=folder_changes
            )

        # Build all qnames that need to be checked
        qnames_to_check: List[str] = []
        # qname -> (display_name, path_so_far, is_file_node, idx)
        qname_paths: Dict[str, tuple] = {}
        current_qname = self.project_node.name

        for idx, part in enumerate(rel_parts):
            is_last = idx == len(rel_parts) - 1
            is_file_node = terminal_type == ScopeType.FILE and is_last
            display_name = Path(part).stem if is_file_node else part
            current_qname = f"{current_qname}.{display_name}"
            path_so_far = self.project_path / Path(*rel_parts[: idx + 1])
            qnames_to_check.append(current_qname)
            qname_paths[current_qname] = (
                display_name, str(path_so_far), is_file_node, idx
            )

        # Batch check all qnames at once
        existing_scopes = await self.manager.batch_get_scopes_by_qnames(
            qnames_to_check
        )

        # Collect scopes to create and relationships to link
        scopes_to_create: List[ScopeModel] = []
        relationships_to_link: List[dict[str, str]] = []
        scope_map: Dict[str, ScopeModel] = {}  # qname -> scope
        current_parent = root
        file_scope: Optional[ScopeModel] = None
        hierarchy_changed = False

        for idx, part in enumerate(rel_parts):
            is_last = idx == len(rel_parts) - 1
            is_file_node = terminal_type == ScopeType.FILE and is_last
            qname = qnames_to_check[idx]
            display_name, path_so_far, _, _ = qname_paths[qname]
            current_qname = qname

            scope = existing_scopes.get(current_qname)

            if not scope:
                # Need to create this scope
                scope_type = ScopeType.FILE if is_file_node else ScopeType.FOLDER
                scope = ScopeModel(
                    id=str(uuid.uuid4()),
                    name=display_name,
                    qname=current_qname,
                    type=scope_type,
                    file_path=path_so_far,
                    start_line=0,
                    start_col=0,
                    end_line=0,
                    end_col=0,
                    checksum=checksum if is_file_node else None,
                )
                scopes_to_create.append(scope)
                if current_parent:
                    relationships_to_link.append({
                        "parent_id": current_parent.id,
                        "child_id": scope.id
                    })
                if scope_type == ScopeType.FOLDER:
                    folder_changes.append(
                        FolderChange(scope=scope, action="created")
                    )
                    self._touched_folder_ids.add(scope.id)
                    folder_chain.append(
                        {"scope": scope, "parent": current_parent}
                    )
                else:
                    file_scope = scope
                hierarchy_changed = True
            else:
                if is_file_node:
                    file_scope = scope
                    checksum_changed = (
                        checksum is not None
                        and scope.checksum != checksum
                    )
                    if checksum_changed:
                        scope.checksum = checksum
                        scope = await self.manager.update_scope(scope)
                        hierarchy_changed = True
                else:
                    folder_chain.append(
                        {"scope": scope, "parent": current_parent}
                    )

            scope_map[current_qname] = scope
            current_parent = scope

        # Batch create all scopes
        if scopes_to_create:
            await self.manager.batch_create_scopes(scopes_to_create)

        # Batch link all parent-child relationships
        if relationships_to_link:
            await self.manager.batch_link_parent_child(
                relationships_to_link
            )

        if not file_scope and terminal_type == ScopeType.FILE:
            logger.error("Failed to build hierarchy for %s", rel_path)
            return None

        if hierarchy_changed:
            skip_last = terminal_type == ScopeType.FOLDER
            self._bubble_folder_chain(
                folder_chain, folder_changes, skip_last=skip_last)

        terminal_scope = (
            file_scope
            if terminal_type == ScopeType.FILE
            else folder_chain[-1]["scope"]
        )
        return HierarchyBuildResult(
            scope=terminal_scope, folder_changes=folder_changes
        )

    async def _ensure_root(self, folder_changes: List[FolderChange]) -> ScopeModel:
        current_qname = self.project_node.name
        root = await self.manager.get_scope_by_qname(current_qname)
        if root:
            return root

        root = await self.manager.create_scope(
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
