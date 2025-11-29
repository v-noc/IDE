from typing import Dict, List
from dataclasses import dataclass
from app.core.parser.scope_manager.repository import ScopeRepository

@dataclass
class ChangeSet:
    new_files: List[str]
    modified_files: List[str]
    deleted_files: List[str]

    def has_changes(self) -> bool:
        return bool(self.new_files or self.modified_files or self.deleted_files)

    def __str__(self):
        return (
            f"ChangeSet(new={len(self.new_files)}, "
            f"modified={len(self.modified_files)}, "
            f"deleted={len(self.deleted_files)})"
        )

class ChangeDetector:
    def __init__(self, scope_manager: ScopeManager):
        self.manager = scope_manager

    def detect_changes(self, current_files: Dict[str, str]) -> ChangeSet:
        """
        Compare current files from disk with those in the DB.
        """
        # 1. Fetch DB State
        db_scopes = self.manager.get_all_file_scopes()
        db_state = {s.file_path: s.checksum for s in db_scopes}
        
        new_files = []
        modified_files = []
        deleted_files = []
        
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
        
        return ChangeSet(
            new_files=new_files,
            modified_files=modified_files,
            deleted_files=deleted_files
        )
