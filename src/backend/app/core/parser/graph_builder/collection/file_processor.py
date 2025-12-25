import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set

from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel, ScopeType
from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.discovery.change_detector import (
    ChangeSet,
    TrackedPath,
)
from app.core.parser.graph_builder.discovery.scanner import ScanResult

logger = logging.getLogger(__name__)


class FileProcessor:
    """
    Handles file scope synchronization using ID-first optimization.
    Ensures File Scopes exist and are linked to correct parents before content analysis.
    """

    def __init__(self, project_node: ProjectNode, scope_manager: ScopeManager):
        self.project_node = project_node
        self.project_path = Path(project_node.path)
        self.manager = scope_manager

    async def process_batch(
        self,
        change_set: ChangeSet,
        scan_result: ScanResult,
        batch_size: int = 100
    ) -> None:
        """
        Synchronize file scopes (Shells) using ID-first events.
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

        existing_by_id = await self.manager.batch_get_scopes_by_ids(ids)

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

        parent_scopes_by_qname: Dict[str, ScopeModel] = {}
        if parent_qnames_needed:
            parent_scopes_by_qname = await self.manager.batch_get_scopes_by_qnames(
                sorted(parent_qnames_needed)
            )

        scopes_to_create: List[ScopeModel] = []
        scopes_to_update: List[ScopeModel] = []
        relationships_to_relink: List[dict[str, str]] = []

        # Get root scope for fallback
        root_scope = await self.manager.get_scope_by_qname(self.project_node.name)
        if not root_scope:
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
            desired_file_path = str(abs_path)
            checksum = scan_result.files.get(tp.path)

            scope = existing_by_id.get(tp.id)
            if not scope:
                scope = ScopeModel(
                    id=tp.id,
                    name=desired_name,
                    qname=desired_qname,
                    type=ScopeType.FILE,
                    file_path=desired_file_path,
                    start_line=0,
                    start_col=0,
                    end_line=0,
                    end_col=0,
                    checksum=checksum,
                )
                scopes_to_create.append(scope)
            else:
                changed = (
                    scope.name != desired_name
                    or scope.qname != desired_qname
                    or scope.file_path != desired_file_path
                    or (checksum and scope.checksum != checksum)
                )
                if changed:
                    scope.name = desired_name
                    scope.qname = desired_qname
                    scope.file_path = desired_file_path
                    if checksum:
                        scope.checksum = checksum
                    scopes_to_update.append(scope)

            # Link/Relink Parent
            parent_id = self.resolve_parent_id(
                abs_path=abs_path,
                root_scope=root_scope,
                folder_path_to_id=folder_path_to_id,
                parent_scopes_by_qname=parent_scopes_by_qname,
            )

            if parent_id:
                # Use batch_relink_parent_child to ensure we remove any old parent link
                # This is critical for moves (file now has a new parent)
                relationships_to_relink.append(
                    {"parent_id": parent_id, "child_id": tp.id}
                )
            else:
                logger.warning(f"Could not resolve parent for file {tp.path}")

        if scopes_to_create:
            await self.manager.batch_create_scopes(scopes_to_create)
        if scopes_to_update:
            await self.manager.batch_update_scopes(scopes_to_update)
        if relationships_to_relink:
            # We use batch_relink_parent_child instead of link_parent_child
            # This handles both new links (no previous parent) and moves (delete old parent link)
            await self.manager.batch_relink_parent_child(relationships_to_relink)

    def qname_for_rel_path(self, rel_path: Path, is_file: bool = False) -> str:
        parts = [p for p in rel_path.parts if p]
        if not parts:
            return self.project_node.name

        qname = ".".join([self.project_node.name] + parts)
        if is_file:
            # File QName usually includes the file stem (module name)
            # parts[-1] is the filename (e.g. 'main.py').
            # We want 'root.main'.
            # Path(p).stem handles 'main.py' -> 'main'.
            # But rel_path parts are strings.
            # Reconstruct to be safe.
            # qname above uses full filename 'root.main.py' which might be wrong for Python.
            # Typically QName for python file 'a/b.py' is 'a.b'.
            # HierarchyBuilder logic was:
            # display_name = Path(part).stem if is_file_node else part
            # current_qname = f"{current_qname}.{display_name}"

            # Let's match HierarchyBuilder logic exactly.
            q_parts = [self.project_node.name]
            for idx, part in enumerate(parts):
                is_last = idx == len(parts) - 1
                name = Path(part).stem if (is_last and is_file) else part
                q_parts.append(name)
            return ".".join(q_parts)

        return qname

    def resolve_parent_id(
        self,
        *,
        abs_path: Path,
        root_scope: ScopeModel,
        folder_path_to_id: Dict[str, str],
        parent_scopes_by_qname: Dict[str, ScopeModel],
    ) -> Optional[str]:
        parent_abs = abs_path.parent
        if str(parent_abs) == str(self.project_path):
            return root_scope.id

        parent_id = folder_path_to_id.get(str(parent_abs))
        if parent_id:
            return parent_id

        try:
            rel_parent = parent_abs.relative_to(self.project_path)
        except ValueError:
            return None

        parent_qname = self.qname_for_rel_path(rel_parent)
        parent_scope = parent_scopes_by_qname.get(parent_qname)
        return parent_scope.id if parent_scope else None
