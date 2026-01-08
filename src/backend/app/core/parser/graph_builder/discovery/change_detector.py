from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, Any

from app.core.parser.graph_builder.collection.file_tracker import FileTracker
from app.core.parser.graph_builder.collection.folder_tracker import (
    FolderTracker,
)
from app.core.repository import Repositories
from app.core.parser.graph_builder.discovery.scanner import ScanResult


@dataclass
class TrackedPath:
    path: str
    id: str


@dataclass
class MoveEvent:
    id: str
    old: str
    new: str


@dataclass
class ChangeSet:
    new_files: List[TrackedPath]
    modified_files: List[TrackedPath]
    deleted_files: List[TrackedPath]
    new_folders: List[TrackedPath]
    deleted_folders: List[TrackedPath]
    moved_files: List[MoveEvent]
    moved_folders: List[MoveEvent]

    def has_changes(self) -> bool:
        return bool(
            self.new_files
            or self.modified_files
            or self.deleted_files
            or self.moved_files
        )

    def has_folder_changes(self) -> bool:
        return bool(
            self.new_folders or self.deleted_folders or self.moved_folders
        )

    def __str__(self):
        return (
            f"ChangeSet(new_files={len(self.new_files)}, "
            f"modified_files={len(self.modified_files)}, "
            f"deleted_files={len(self.deleted_files)}, "
            f"new_folders={len(self.new_folders)}, "
            f"deleted_folders={len(self.deleted_folders)}, "
            f"moved_files={len(self.moved_files)}, "
            f"moved_folders={len(self.moved_folders)})"
        )


class ChangeDetector:
    def __init__(self, repos: Repositories):
        self.repos = repos
        self.file_tracker = FileTracker()
        self.folder_tracker = FolderTracker()

    async def _get_or_create_file_id(self, file_path: str) -> str:
        """
        Ensure a FileID exists (via FileTracker) and return it.
        Runs in a thread because FileTracker uses libcst + disk IO.
        """
        return await asyncio.to_thread(
            self.file_tracker.process_file,
            Path(file_path),
        )

    async def _get_or_create_folder_id(self, folder_path: str) -> str:
        """
        Ensure a FolderID exists (via FolderTracker) and return it.
        Runs in a thread because FolderTracker touches the filesystem.
        """
        return await asyncio.to_thread(
            self.folder_tracker.ensure_tracking,
            Path(folder_path),
        )

    def _compute_file_changes(
        self,
        current_files: Dict[str, str],
        db_file_snapshots: List[Dict[str, Any]],
    ) -> Tuple[List[str], List[str], List[str], Dict[str, str]]:
        """
        Returns (new_files, modified_files, deleted_files, db_id_by_path).
        """
        db_state = {f["path"]: f["checksum"] for f in db_file_snapshots}
        db_id_by_path = {f["path"]: f["id"] for f in db_file_snapshots}

        current_paths = set(current_files.keys())
        db_paths = set(db_state.keys())

        new_files = sorted(current_paths - db_paths)
        deleted_files = sorted(db_paths - current_paths)

        intersection = current_paths & db_paths
        modified_files = sorted(
            [
                p
                for p in intersection
                if current_files.get(p) != db_state.get(p)
            ]
        )

        return new_files, modified_files, deleted_files, db_id_by_path

    def _compute_folder_changes(
        self,
        current_folders: Set[str],
        db_folder_snapshots: List[Dict[str, Any]],
    ) -> Tuple[List[str], List[str], Dict[str, str]]:
        """
        Returns (new_folders, deleted_folders, db_id_by_path).
        """
        db_folder_paths: Set[str] = {
            f["path"] for f in db_folder_snapshots
        }
        db_id_by_path = {
            f["path"]: f["id"] for f in db_folder_snapshots
        }

        new_folders = sorted(current_folders - db_folder_paths)
        deleted_folders = sorted(db_folder_paths - current_folders)

        return new_folders, deleted_folders, db_id_by_path

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
                return p, await extractor(p)

        return await asyncio.gather(*(_one(p) for p in paths))

    async def _reconcile_moves(
        self,
        *,
        potential_new_paths: List[str],
        potential_deleted: List[TrackedPath],
        id_extractor,
        max_concurrency: int = 50,
    ) -> Tuple[List[TrackedPath], List[TrackedPath], List[MoveEvent]]:
        """
        Reconcile moves by reading IDs only for potential-new paths and
        matching
        them against the IDs of potential-deleted paths.
        """
        deleted_by_id: Dict[str, TrackedPath] = {
            d.id: d for d in potential_deleted
        }

        moved: List[MoveEvent] = []
        remaining_new: Dict[str, TrackedPath] = {}
        remaining_deleted: Dict[str, TrackedPath] = {
            d.path: d for d in potential_deleted
        }

        extracted = await self._gather_ids(
            potential_new_paths,
            id_extractor,
            max_concurrency=max_concurrency,
        )
        for new_path, stable_id in extracted:
            if not stable_id:
                # Track even if id extraction failed (should be rare; tracker
                # normally returns a UUID fallback)
                remaining_new[new_path] = TrackedPath(path=new_path, id="")
                continue

            new_item = TrackedPath(path=new_path, id=stable_id)
            old_item = deleted_by_id.get(stable_id)
            if not old_item:
                remaining_new[new_path] = new_item
                continue
            moved.append(
                MoveEvent(
                    id=stable_id,
                    old=old_item.path,
                    new=new_item.path,
                )
            )
            remaining_deleted.pop(old_item.path, None)

        return (
            sorted(remaining_new.values(), key=lambda x: x.path),
            sorted(remaining_deleted.values(), key=lambda x: x.path),
            moved,
        )

    async def detect_changes(self, scan_result: ScanResult, project_id: str) -> ChangeSet:
        """
        Compare current files from disk with those in the DB.
        """
        current_files = scan_result.files
        current_folders = scan_result.folders

        # 1) Fetch DB state in parallel
        db_file_snapshots, db_folder_snapshots = await asyncio.gather(
            self.repos.file_repo.get_project_files(project_id),
            self.repos.folder_repo.get_project_folders(project_id),
        )

        (
            new_files,
            modified_files,
            deleted_files,
            db_file_id_by_path,
        ) = self._compute_file_changes(current_files, db_file_snapshots)

        (
            new_folders,
            deleted_folders,
            db_folder_id_by_path,
        ) = self._compute_folder_changes(current_folders, db_folder_snapshots)

        # Convert DB-derived sets to tracked paths (path + stable id)
        modified_files_tracked = [
            TrackedPath(path=p, id=db_file_id_by_path[p])
            for p in modified_files
            if p in db_file_id_by_path
        ]
        deleted_files_tracked = [
            TrackedPath(path=p, id=db_file_id_by_path[p])
            for p in deleted_files
            if p in db_file_id_by_path
        ]
        deleted_folders_tracked = [
            TrackedPath(path=p, id=db_folder_id_by_path[p])
            for p in deleted_folders
            if p in db_folder_id_by_path
        ]

        # 2) Reconcile moves by extracting IDs concurrently (only on "new"
        # paths)
        (
            new_files_tracked,
            deleted_files_tracked,
            moved_files,
        ) = await self._reconcile_moves(
            potential_new_paths=new_files,
            potential_deleted=deleted_files_tracked,
            id_extractor=self._get_or_create_file_id,
            max_concurrency=50,
        )

        (
            new_folders_tracked,
            deleted_folders_tracked,
            moved_folders,
        ) = await self._reconcile_moves(
            potential_new_paths=new_folders,
            potential_deleted=deleted_folders_tracked,
            id_extractor=self._get_or_create_folder_id,
            max_concurrency=50,
        )

        return ChangeSet(
            new_files=new_files_tracked,
            modified_files=modified_files_tracked,
            deleted_files=deleted_files_tracked,
            new_folders=new_folders_tracked,
            deleted_folders=deleted_folders_tracked,
            moved_files=moved_files,
            moved_folders=moved_folders,
        )
