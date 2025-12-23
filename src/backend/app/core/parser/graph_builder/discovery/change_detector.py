from typing import List, Set
from dataclasses import dataclass
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.graph_builder.discovery.scanner import ScanResult


@dataclass
class ChangeSet:
    new_files: List[str]
    modified_files: List[str]
    deleted_files: List[str]
    new_folders: List[str]
    deleted_folders: List[str]

    def has_changes(self) -> bool:
        return bool(self.new_files or self.modified_files or self.deleted_files)

    def has_folder_changes(self) -> bool:
        return bool(self.new_folders or self.deleted_folders)

    def __str__(self):
        return (
            f"ChangeSet(new_files={len(self.new_files)}, "
            f"modified_files={len(self.modified_files)}, "
            f"deleted_files={len(self.deleted_files)}, "
            f"new_folders={len(self.new_folders)}, "
            f"deleted_folders={len(self.deleted_folders)})"
        )


class ChangeDetector:
    def __init__(self, scope_manager: ScopeManager):
        self.manager = scope_manager

    async def detect_changes(self, scan_result: ScanResult) -> ChangeSet:
        """
        Compare current files from disk with those in the DB.
        """
        current_files = scan_result.files
        current_folders = scan_result.folders

        # 1. Fetch DB State
        db_scopes = await self.manager.get_all_file_scopes()

        db_state = {s.file_path: s.checksum for s in db_scopes}
        db_folders = await self.manager.get_all_folder_scopes()
        db_folder_paths: Set[str] = {folder.file_path for folder in db_folders}

        new_files = []
        modified_files = []
        deleted_files = []
        new_folders = []
        deleted_folders = []

        all_paths = set(current_files.keys()) | set(db_state.keys())

        for path in all_paths:
            in_disk = path in current_files
            in_db = path in db_state

            if in_disk and not in_db:
                new_files.append(path)
            elif in_db and not in_disk:
                deleted_files.append(path)
            elif in_disk and in_db:
                if current_files[path] != db_state[path]:
                    modified_files.append(path)

        current_folder_paths = current_folders
        new_folders = [
            folder for folder in current_folder_paths
            if folder not in db_folder_paths
        ]
        deleted_folders = [
            folder for folder in db_folder_paths
            if folder not in current_folder_paths
        ]

        return ChangeSet(
            new_files=new_files,
            modified_files=modified_files,
            deleted_files=deleted_files,
            new_folders=new_folders,
            deleted_folders=deleted_folders,
        )
