import hashlib
import os
import logging
from pathlib import Path
from typing import Dict, Optional
import pathspec

logger = logging.getLogger(__name__)

class FileScanner:
    def __init__(self, project_path: str, ignore_file_name: str = ".gitignore"):
        self.project_path = Path(project_path)
        self.ignore_file_name = ignore_file_name
        self.spec = self._load_ignore_spec()

    def _load_ignore_spec(self) -> Optional[pathspec.PathSpec]:
        ignore_file = self.project_path / self.ignore_file_name
        if ignore_file.is_file():
            try:
                with open(ignore_file, "r") as f:
                    return pathspec.PathSpec.from_lines("gitwildmatch", f)
            except Exception as e:
                logger.warning(f"Failed to load ignore file {ignore_file}: {e}")
        return None

    def scan(self) -> Dict[str, str]:
        """
        Scan all .py files in the project directory and calculate their checksums.
        Returns: Dict[absolute_file_path, checksum]
        """
        file_map = {}
        
        for root, dirs, files in os.walk(self.project_path):
            # Filter directories using pathspec
            root_path = Path(root)
            rel_root = root_path.relative_to(self.project_path)
            
            # Prune ignored directories
            dirs[:] = [
                d for d in dirs 
                if not self._is_ignored(rel_root / d)
            ]
            
            for file in files:
                if file.endswith(".py"):
                    file_path = root_path / file
                    rel_path = file_path.relative_to(self.project_path)
                    
                    if self._is_ignored(rel_path):
                        continue
                        
                    try:
                        checksum = self._calculate_checksum(file_path)
                        file_map[str(file_path.absolute())] = checksum
                    except Exception as e:
                        logger.error(f"Error scanning file {file_path}: {e}")
                        
        return file_map

    def _is_ignored(self, rel_path: Path) -> bool:
        if self.spec:
            return self.spec.match_file(str(rel_path))
        return False

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
