from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from app.core.model.schemas import FileSchema, FolderSchema
from app.core.model.schemas.structure_schema import INIT_FOLDER_ID

from app.core.parser.drivers import DriverManager
from app.core.repository import Repositories
from app.core.parser.graph_builder.discovery.scanner import ScanResult
from app.core.model.nodes import FileNode, FolderNode

logger = logging.getLogger(__name__)


@dataclass
class TrackedPath:
    path: str
    id: str
    parent_id: Optional[str] = None


@dataclass
class MoveEvent:
    id: str
    old: str
    new_path: str
    new_parent_id: Optional[str] = None


@dataclass
class ChangeSet:
    new_files: List[TrackedPath]
    modified_files: List[TrackedPath]
    deleted_files: List[TrackedPath]
    new_folders: List[TrackedPath]
    modified_folders: List[TrackedPath]
    deleted_folders: List[TrackedPath]
    moved_files: List[MoveEvent]
    moved_folders: List[MoveEvent]

    def has_changes(self) -> bool:
        return bool(
            self.new_files
            or self.modified_files
            or self.deleted_files
            or self.moved_files
            or self.new_folders
            or self.modified_folders
            or self.deleted_folders
            or self.moved_folders
        )

    def has_folder_changes(self) -> bool:
        return bool(
            self.new_folders
            or self.modified_folders
            or self.deleted_folders
            or self.moved_folders
        )

    def __str__(self):
        return (
            f"ChangeSet(new_files={len(self.new_files)}, "
            f"modified_files={len(self.modified_files)}, "
            f"deleted_files={len(self.deleted_files)}, "
            f"new_folders={len(self.new_folders)}, "
            f"modified_folders={len(self.modified_folders)}, "
            f"deleted_folders={len(self.deleted_folders)}, "
            f"moved_files={len(self.moved_files)}, "
            f"moved_folders={len(self.moved_folders)})"
        )


class ChangeDetector:
    def __init__(self, repos: Repositories, driver_manager: DriverManager):
        self.repos = repos
        self.driver_manager = driver_manager

    async def _get_or_create_file_id(self, file_path: str) -> str:
        driver = await self.driver_manager.get_driver(file_path)
        result = await driver.read_or_inject_file_id(file_path)
        return result.file_id

    async def _get_or_create_folder_id(self, folder_path: str) -> str:
        driver = await self.driver_manager.get_driver_for_folder(folder_path)
        result = await driver.read_or_inject_folder_id(folder_path)
        return result.folder_id

    @staticmethod
    def _extract_child_id(child: Any) -> Optional[str]:
        if isinstance(child, str):
            return child
        child_id = getattr(child, "id", None)
        if isinstance(child_id, str):
            return child_id
        return None

    def _build_parent_maps(
        self,
        db_folder_snapshots: List[FolderNode],
    ) -> Tuple[Dict[str, Optional[str]], Dict[str, Optional[str]]]:
        """
        Build parent maps:
          - folder_parent_by_id: folder_id -> parent_folder_id (or None for root)
          - file_parent_by_id: file_id -> parent_folder_id (or None for root)
        """
        folder_parent_by_id: Dict[str, Optional[str]] = {}
        file_parent_by_id: Dict[str, Optional[str]] = {}

        for folder in db_folder_snapshots:
            if folder.id and folder.id not in folder_parent_by_id:
                folder_parent_by_id[folder.id] = None

            children_by_type = folder.children_by_type or {}
            for child in children_by_type.get("folder_children", []):
                child_id = self._extract_child_id(child)
                if child_id:
                    folder_parent_by_id[child_id] = folder.id
            for child in children_by_type.get("file_children", []):
                child_id = self._extract_child_id(child)
                if child_id:
                    file_parent_by_id[child_id] = folder.id

        return folder_parent_by_id, file_parent_by_id

    async def _gather_ids(
        self,
        paths: Iterable[str],
        extractor,
        *,
        max_concurrency: int = 50,
    ) -> List[Tuple[str, Optional[str]]]:
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _one(p: str) -> Tuple[str, Optional[str]]:
            async with semaphore:
                try:
                    return p, await extractor(p)
                except Exception:
                    logger.warning(
                        "Stable id lookup failed for %s; path will be omitted "
                        "from id-based change detection for this run.",
                        p,
                        exc_info=True,
                    )
                    return p, None

        return await asyncio.gather(*(_one(p) for p in paths))

    @staticmethod
    def _invert_path_id_map(path_to_id: Dict[str, str]) -> Dict[str, str]:
        """
        Build id -> path map from path -> id.
        If duplicate IDs appear, later sorted paths win for determinism.
        """
        id_to_path: Dict[str, str] = {}
        for path in sorted(path_to_id.keys()):
            stable_id = path_to_id[path]
            if stable_id:
                id_to_path[stable_id] = path
        return id_to_path

    async def _extract_current_path_to_id(
        self,
        *,
        paths: Iterable[str],
        id_extractor,
        max_concurrency: int = 50,
    ) -> Dict[str, str]:
        extracted = await self._gather_ids(
            paths,
            id_extractor,
            max_concurrency=max_concurrency,
        )
        return {path: stable_id for path, stable_id in extracted if stable_id}

    @staticmethod
    def _build_current_parent_maps(
        *,
        current_folder_id_by_path: Dict[str, str],
        current_file_id_by_path: Dict[str, str],
    ) -> Tuple[Dict[str, Optional[str]], Dict[str, Optional[str]]]:
        """
        Build parent maps from current filesystem scan.
        """
        current_folder_parent_by_id: Dict[str, Optional[str]] = {}
        current_file_parent_by_id: Dict[str, Optional[str]] = {}

        for folder_path, folder_id in current_folder_id_by_path.items():
            parent_path = str(Path(folder_path).parent)
            current_folder_parent_by_id[folder_id] = current_folder_id_by_path.get(
                parent_path
            )

        for file_path, file_id in current_file_id_by_path.items():
            parent_path = str(Path(file_path).parent)

            current_file_parent_by_id[file_id] = current_folder_id_by_path.get(
                parent_path
            )

        return current_folder_parent_by_id, current_file_parent_by_id

    @staticmethod
    def _sorted_tracked(items: List[TrackedPath]) -> List[TrackedPath]:
        return sorted(items, key=lambda x: x.path)

    def _classify_folder_changes(
        self,
        *,
        db_folders_by_id: Dict[str, FolderNode],
        current_folder_path_by_id: Dict[str, str],
        db_folder_parent_by_id: Dict[str, Optional[str]],
        current_folder_parent_by_id: Dict[str, Optional[str]],
    ) -> Tuple[List[TrackedPath], List[TrackedPath], List[TrackedPath], List[MoveEvent]]:
        """
        ID-first folder classification.
        """
        db_ids = set(db_folders_by_id.keys())
        current_ids = set(current_folder_path_by_id.keys())

        new_ids = current_ids - db_ids
        deleted_ids = db_ids - current_ids
        common_ids = db_ids & current_ids

        new_folders = [
            TrackedPath(
                path=current_folder_path_by_id[item_id],
                id=item_id,
                parent_id=current_folder_parent_by_id.get(item_id),
            )
            for item_id in new_ids
        ]
        deleted_folders = [
            TrackedPath(
                path=db_folders_by_id[item_id].path,
                id=item_id,
                parent_id=db_folder_parent_by_id.get(item_id),
            )
            for item_id in deleted_ids
        ]

        moved: List[MoveEvent] = []
        modified_folders: List[TrackedPath] = []
        for item_id in common_ids:
            db_node = db_folders_by_id[item_id]
            current_path = current_folder_path_by_id[item_id]
            db_parent = db_folder_parent_by_id.get(item_id)
            current_parent = current_folder_parent_by_id.get(item_id)

            if db_parent != current_parent:
                moved.append(
                    MoveEvent(
                        id=item_id,
                        old=db_node.path,
                        new_path=current_path,
                        new_parent_id=current_parent,
                    )
                )
                continue

            if db_node.path != current_path:
                modified_folders.append(
                    TrackedPath(
                        path=current_path,
                        id=item_id,
                        parent_id=current_parent,
                    )
                )

        return (
            self._sorted_tracked(new_folders),
            self._sorted_tracked(modified_folders),
            self._sorted_tracked(deleted_folders),
            moved,
        )

    def _classify_file_changes(
        self,
        *,
        db_files_by_id: Dict[str, FileNode],
        current_file_path_by_id: Dict[str, str],
        current_file_hash_by_id: Dict[str, str],
        db_file_parent_by_id: Dict[str, Optional[str]],
        current_file_parent_by_id: Dict[str, Optional[str]],
    ) -> Tuple[List[TrackedPath], List[TrackedPath], List[TrackedPath], List[MoveEvent]]:
        """
        ID-first file classification.
        """
        db_ids = set(db_files_by_id.keys())
        current_ids = set(current_file_path_by_id.keys())

        new_ids = current_ids - db_ids
        deleted_ids = db_ids - current_ids
        common_ids = db_ids & current_ids

        new_files = [
            TrackedPath(
                path=current_file_path_by_id[item_id],
                id=item_id,
                parent_id=current_file_parent_by_id.get(item_id),
            )
            for item_id in new_ids
        ]
        deleted_files = [
            TrackedPath(
                path=db_files_by_id[item_id].path,
                id=item_id,
                parent_id=db_file_parent_by_id.get(item_id),
            )
            for item_id in deleted_ids
        ]

        moved: List[MoveEvent] = []
        modified_files: List[TrackedPath] = []
        for item_id in common_ids:
            db_node = db_files_by_id[item_id]
            current_path = current_file_path_by_id[item_id]
            current_hash = current_file_hash_by_id.get(item_id)
            db_parent = db_file_parent_by_id.get(item_id)
            current_parent = current_file_parent_by_id.get(item_id)

            if db_parent != current_parent:
                moved.append(
                    MoveEvent(
                        id=item_id,
                        old=db_node.path,
                        new_path=current_path,
                        new_parent_id=current_parent,
                    )
                )
                continue

            path_changed = db_node.path != current_path
            hash_changed = current_hash is not None and db_node.hash != current_hash
            if path_changed or hash_changed:
                modified_files.append(
                    TrackedPath(
                        path=current_path,
                        id=item_id,
                        parent_id=current_parent,
                    )
                )

        return (
            self._sorted_tracked(new_files),
            self._sorted_tracked(modified_files),
            self._sorted_tracked(deleted_files),
            moved,
        )

    async def detect_changes(self, scan_result: ScanResult) -> ChangeSet:
        """
        Compare current filesystem state with DB state using stable IDs.
        """
        current_files_by_path = scan_result.files
        current_folder_paths = scan_result.folders

        # 1) Fetch DB state in parallel
        db_file_snapshots, db_folder_snapshots = await asyncio.gather(
            self.repos.structure_repo.get_all(doc_type=FileSchema.__name__),
            self.repos.structure_repo.get_all(doc_type=FolderSchema.__name__),
        )

        # Virtual global root from bootstrap (FolderSchema.create_init_folder); not on disk.
        db_folder_snapshots = [
            n for n in db_folder_snapshots if n.id != INIT_FOLDER_ID
        ]

        # 2) Extract stable IDs for all currently scanned paths.
        current_folder_id_by_path = await self._extract_current_path_to_id(
            paths=current_folder_paths,
            id_extractor=self._get_or_create_folder_id,
            max_concurrency=50,
        )
        current_file_id_by_path = await self._extract_current_path_to_id(
            paths=current_files_by_path.keys(),
            id_extractor=self._get_or_create_file_id,
            max_concurrency=50,
        )

        current_folder_path_by_id = self._invert_path_id_map(
            current_folder_id_by_path)
        current_file_path_by_id = self._invert_path_id_map(
            current_file_id_by_path)
        current_file_hash_by_id: Dict[str, str] = {
            item_id: current_files_by_path[path]
            for item_id, path in current_file_path_by_id.items()
            if path in current_files_by_path
        }

        # 3) Build parent maps.
        db_folder_parent_by_id, db_file_parent_by_id = self._build_parent_maps(
            db_folder_snapshots
        )

        current_folder_parent_by_id, current_file_parent_by_id = (
            self._build_current_parent_maps(
                current_folder_id_by_path=current_folder_id_by_path,
                current_file_id_by_path=current_file_id_by_path,
            )
        )

        db_folders_by_id: Dict[str, FolderNode] = {
            node.id: node for node in db_folder_snapshots if node.id
        }
        db_files_by_id: Dict[str, FileNode] = {
            node.id: node for node in db_file_snapshots if node.id
        }

        # 4) ID-first classification.
        (
            new_folders_tracked,
            modified_folders_tracked,
            deleted_folders_tracked,
            moved_folders,
        ) = self._classify_folder_changes(
            db_folders_by_id=db_folders_by_id,
            current_folder_path_by_id=current_folder_path_by_id,
            db_folder_parent_by_id=db_folder_parent_by_id,
            current_folder_parent_by_id=current_folder_parent_by_id,
        )

        (
            new_files_tracked,
            modified_files_tracked,
            deleted_files_tracked,
            moved_files,
        ) = self._classify_file_changes(
            db_files_by_id=db_files_by_id,
            current_file_path_by_id=current_file_path_by_id,
            current_file_hash_by_id=current_file_hash_by_id,
            db_file_parent_by_id=db_file_parent_by_id,
            current_file_parent_by_id=current_file_parent_by_id,
        )

        return ChangeSet(
            new_files=new_files_tracked,
            modified_files=modified_files_tracked,
            deleted_files=deleted_files_tracked,
            new_folders=new_folders_tracked,
            modified_folders=modified_folders_tracked,
            deleted_folders=deleted_folders_tracked,
            moved_files=moved_files,
            moved_folders=moved_folders,
        )
