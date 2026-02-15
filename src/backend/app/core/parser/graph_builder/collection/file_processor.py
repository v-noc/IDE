import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set

from app.core.repository.structure.file_repo import FileRepo
from app.core.repository.structure.folder_repo import FolderRepo
from app.core.model.nodes import ProjectNode, FileNode, FolderNode
from app.core.parser.graph_builder.discovery.change_detector import (
    ChangeSet,
    TrackedPath,
)
from app.core.parser.graph_builder.discovery.scanner import ScanResult

logger = logging.getLogger(__name__)


class FileProcessor:
    """
    Handles file scope synchronization using ID-first optimization.
    Ensures File Nodes exist and are linked to correct parents before content analysis.
    """

    def __init__(self, project_node: ProjectNode, file_repo: FileRepo, folder_repo: FolderRepo):
        self.project_node = project_node
        self.project_path = Path(project_node.path)
        self.file_repo = file_repo
        self.folder_repo = folder_repo

    async def process_batch(
        self,
        change_set: ChangeSet,
        scan_result: ScanResult,
        batch_size: int = 100
    ) -> None:
        """
        Synchronize file nodes (Shells) using ID-first events.
        """
        # 1. Collect all folders that might be parents (newly created or moved folders)
        # This helps resolving parent IDs without hitting DB if they are in the change set
        folder_path_to_id: Dict[str, str] = {
            tp.path: tp.id for tp in change_set.new_folders
        }
        folder_path_to_id.update(
            {mv.new: mv.id for mv in change_set.moved_folders})

        # 2. Process Moves (Update Location & Parent)
        moved_tracked = [TrackedPath(path=mv.new, id=mv.id)
                         for mv in change_set.moved_files]

        await self._upsert_files_in_batches(
            files=moved_tracked,
            folder_path_to_id=folder_path_to_id,
            scan_result=scan_result,
            batch_size=batch_size,
        )

        # 3. Process New Files (Create Shell)
        await self._upsert_files_in_batches(
            files=change_set.new_files,
            folder_path_to_id=folder_path_to_id,
            scan_result=scan_result,
            batch_size=batch_size,
        )

        # 4. Process Modified Files
        # Modified files usually just need content analysis, but we ensure they exist/checksum update
        # We can optionally update their checksum here if we want to be safe,
        # but content analysis will do it too.
        # For optimization, we can batch update checksums here if provided in scan_result.
        await self._upsert_files_in_batches(
            files=change_set.modified_files,
            folder_path_to_id=folder_path_to_id,
            scan_result=scan_result,
            batch_size=batch_size,
        )

        # 5. Batch delete files by stable id (mirror FolderProcessor behavior)
        if change_set.deleted_files:
            deleted_ids = [tp.id for tp in change_set.deleted_files if tp.id]
            if deleted_ids:
                # chunk to avoid very large AQL bind vars / loops
                for i in range(0, len(deleted_ids), batch_size):
                    batch_ids = deleted_ids[i: i + batch_size]
                    await self.file_repo.delete_batch(batch_ids)
                logger.info("Deleted %d file(s) in batch", len(deleted_ids))

    async def _upsert_files_in_batches(
        self,
        *,
        files: List[TrackedPath],
        folder_path_to_id: Dict[str, str],
        scan_result: ScanResult,
        batch_size: int,
    ) -> None:
        if not files:
            return

        for i in range(0, len(files), batch_size):
            batch = files[i: i + batch_size]
            await self._upsert_files_batch(
                batch=batch,
                folder_path_to_id=folder_path_to_id,
                scan_result=scan_result,
            )

    async def _upsert_files_batch(
        self,
        *,
        batch: List[TrackedPath],
        folder_path_to_id: Dict[str, str],
        scan_result: ScanResult,
    ) -> None:
        ids = [tp.id for tp in batch if tp.id]
        if not ids:
            return

        existing_by_id = await self.file_repo.get_by_ids(ids)

        # Pre-fetch parent scopes that are NOT in the change set map
        parent_qnames_needed: Set[str] = set()
        for tp in batch:
            parent_abs = str(Path(tp.path).parent)
            if parent_abs == str(self.project_path):
                continue
            if parent_abs in folder_path_to_id:
                continue
            try:
                rel_parent = Path(parent_abs).relative_to(self.project_path)
                parent_qnames_needed.add(self.qname_for_rel_path(rel_parent))
            except ValueError:
                continue

        parent_nodes_by_qname: Dict[str, FolderNode] = {}
        if parent_qnames_needed:
            parent_nodes_by_qname = await self.folder_repo.get_by_qnames(
                sorted(parent_qnames_needed)
            )

        nodes_to_create: List[FileNode] = []
        nodes_to_update: List[FileNode] = []
        moves_to_execute: List[tuple[str, str]] = []

        # Get root node for fallback
        root_node = self.project_node
        if not root_node:
            # Should exist due to FolderProcessor running first
            logger.warning("Root scope not found during file processing")
            return

        for tp in batch:
            if not tp.id:
                continue

            abs_path = Path(tp.path)
            try:
                rel_path = abs_path.relative_to(self.project_path)
            except ValueError:
                logger.warning(
                    "File %s is not inside project path %s; skipping",
                    tp.path,
                    self.project_path,
                )
                continue

            desired_name = abs_path.stem
            desired_qname = self.qname_for_rel_path(rel_path, is_file=True)
            desired_path = str(abs_path)
            checksum = scan_result.files.get(tp.path)

            node = existing_by_id.get(tp.id)
            if not node:
                node = FileNode(
                    key=tp.id,
                    name=desired_name,
                    qname=desired_qname,
                    path=desired_path,
                    hash=checksum,
                    description=f"File {desired_name}",
                    node_type="file"
                )
                nodes_to_create.append(node)
            else:
                changed = (
                    node.name != desired_name
                    or node.qname != desired_qname
                    or node.path != desired_path
                    or (checksum and node.hash != checksum)
                )
                if changed:
                    node.name = desired_name
                    node.qname = desired_qname
                    node.path = desired_path
                    if checksum:
                        node.hash = checksum
                    nodes_to_update.append(node)

            # Link/Relink Parent
            parent_id = self.resolve_parent_id(
                abs_path=abs_path,
                root_node=root_node,
                folder_path_to_id=folder_path_to_id,
                parent_nodes_by_qname=parent_nodes_by_qname,
            )

            if parent_id:
                moves_to_execute.append((tp.id, parent_id))
            else:
                logger.warning(f"Could not resolve parent for file {tp.path}")

        if nodes_to_create:
            await self.file_repo.create(nodes_to_create)
        if nodes_to_update:
            await self.file_repo.update_batch(nodes_to_update)
        if moves_to_execute:
            await self.file_repo.move_batch(moves_to_execute)

    def qname_for_rel_path(self, rel_path: Path, is_file: bool = False) -> str:
        parts = [p for p in rel_path.parts if p]
        if not parts:
            return self.project_node.name

        if is_file:
            # Match HierarchyBuilder logic exactly.
            q_parts = [self.project_node.name]
            for idx, part in enumerate(parts):
                is_last = idx == len(parts) - 1
                name = Path(part).stem if (is_last and is_file) else part
                q_parts.append(name)
            return ".".join(q_parts)

        return ".".join([self.project_node.name] + parts)

    def resolve_parent_id(
        self,
        *,
        abs_path: Path,
        root_node: FolderNode,
        folder_path_to_id: Dict[str, str],
        parent_nodes_by_qname: Dict[str, FolderNode],
    ) -> Optional[str]:
        parent_abs = abs_path.parent
        if str(parent_abs) == str(self.project_path):
            # Always use self.project_node.id to ensure we use the persisted version
            if not self.project_node.id:
                # Fallback to root_node.id if project_node.id is not set
                return root_node.id if root_node.id else None
            return self.project_node.id

        parent_id = folder_path_to_id.get(str(parent_abs))
        if parent_id:
            return parent_id

        try:
            rel_parent = parent_abs.relative_to(self.project_path)
        except ValueError:
            return None

        parent_qname = self.qname_for_rel_path(rel_parent)
        parent_node = parent_nodes_by_qname.get(parent_qname)
        return parent_node.id if parent_node else None
