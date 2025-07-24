from pathlib import Path
from typing import List, Optional
import pathspec
try:
    import tomllib
except ModuleNotFoundError:
    import toml as tomllib  # type: ignore


class FileNavigator:
    def __init__(self, root_path: str, ignore_file_name: str = ".gitignore"):
        self.root_path = Path(root_path)
       
        self.ignore_file_name = ignore_file_name
        self.spec = self._load_ignore_spec()

    def _load_ignore_spec(self) -> Optional[pathspec.PathSpec]:
        ignore_file = self.root_path / self.ignore_file_name
        if ignore_file.is_file():
                with ignore_file.open("rb") as f:
                    toml_data = tomllib.load(f)
                    patterns = toml_data.get("ignore", {}).get("patterns", [])
                    if patterns:
                        return pathspec.PathSpec.from_lines(
                            "gitwildmatch", patterns
                    )
        return None

    def find_files(self, extensions: Optional[List[str]] = None) -> List[str]:
        found_files = []
        for file_path in self.root_path.rglob("*"):
            if file_path.is_file():
                if (
                    self.spec and self.spec.match_file(
                        str(file_path.relative_to(self.root_path))
                    )
                ):
                    continue
                if extensions:
                    if file_path.suffix in extensions:
                        found_files.append(str(file_path))
                else:
                    found_files.append(str(file_path))
        return found_files
