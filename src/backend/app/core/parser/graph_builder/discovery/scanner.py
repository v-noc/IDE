import hashlib
import os
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set
import pathspec
import tomllib

from app.core.parser.driver_config import python_file_extensions

logger = logging.getLogger(__name__)


def _normalize_extensions(exts: Iterable[str]) -> tuple[str, ...]:
    out: list[str] = []
    for e in exts:
        e = e.lower().strip()
        if not e:
            continue
        out.append(e if e.startswith(".") else f".{e}")
    return tuple(out) if out else (".py",)


@dataclass
class ScanResult:
    files: Dict[str, str]
    folders: Set[str]


class FileScanner:
    def __init__(
        self,
        project_path: str,
        ignore_file_name: str = ".gitignore",
        *,
        extensions: Optional[List[str]] = None,
    ):
        self.project_path = Path(project_path)
        self.ignore_file_name = ignore_file_name
        self.spec = self._load_ignore_spec()
        self._extensions = _normalize_extensions(
            extensions if extensions is not None else python_file_extensions()
        )

    def _load_ignore_spec(self) -> Optional[pathspec.PathSpec]:
        if self.ignore_file_name is None:
            return None

        ignore_file = self.project_path / self.ignore_file_name
        if not ignore_file.is_file():
            return None

        try:
            patterns = self._load_patterns(ignore_file)
            if patterns:
                return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        except Exception as e:
            logger.warning(f"Failed to load ignore file {ignore_file}: {e}")
        return None

    def _load_patterns(self, ignore_file: Path) -> Iterable[str]:
        if ignore_file.suffix == ".toml":
            with ignore_file.open("rb") as f:
                data = tomllib.load(f)
            ignore_section = data.get("ignore", {})
            patterns = ignore_section.get("patterns", [])
            if isinstance(patterns, list):
                return [str(pattern) for pattern in patterns if pattern]
            return []

        with ignore_file.open("r") as f:
            return [line.strip() for line in f if line.strip()]

    def scan(self) -> ScanResult:
        """
        Scan tracked source files (by extension) and calculate checksums.
        Extensions default to the Python driver registry; pass `extensions` to
        align with other language drivers later.
        Returns: ScanResult(files=Dict[path, checksum], folders=Set[absolute_path])
        """
        file_map: Dict[str, str] = {}
        folder_set: Set[str] = {str(self.project_path.absolute())}

        for root, dirs, files in os.walk(self.project_path):
            # Filter directories using pathspec

            root_path = Path(root)
            rel_root = root_path.relative_to(self.project_path)

            folder_set.add(str(root_path.absolute()))

            # Prune ignored directories
            dirs[:] = [
                d for d in dirs
                if not self._is_ignored(rel_root / d)
            ]

            for file in files:

                lower = file.lower()
                if any(lower.endswith(ext) for ext in self._extensions):
                    file_path = root_path / file
                    rel_path = file_path.relative_to(self.project_path)
                    print(f"rel_path: {rel_path}")
                    if self._is_ignored(rel_path):
                        continue

                    try:
                        checksum = self._calculate_checksum(file_path)
                        file_map[str(file_path.absolute())] = checksum
                    except Exception as e:
                        logger.error(f"Error scanning file {file_path}: {e}")

                    # Track folder hierarchy contributed by this file
                    for parent in rel_path.parents:
                        if str(parent) == ".":
                            break
                        folder_set.add(
                            str((self.project_path / parent).absolute()))
        folder_set.remove(str(self.project_path.absolute()))
        return ScanResult(files=file_map, folders=folder_set)

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
