
from typing import List, Optional
from functools import lru_cache
from .models import BaseNode
from .parser import JediParser
from .id_injector import inject_ids


@lru_cache(maxsize=50)
def _inner_scan(content: str):
    # Phase 1: ID Injection
    processed_content, modified = inject_ids(content)

    # Phase 2: Parsing
    parser = JediParser(processed_content)
    nodes = parser.parse()

    return nodes, processed_content, modified


def scan(content: str, file_path: Optional[str] = None) -> tuple[List[BaseNode], str]:
    """
    Scans the content, injects IDs if missing (and updates file), and returns the parsed AST and processed content.
    """
    # Step 1: Inject IDs
    # We only write to file if file_path is provided AND content was modified.
    nodes, processed_content, modified = _inner_scan(content)

    if modified and file_path:
        try:
            with open(file_path, "w") as f:
                f.write(processed_content)
        except Exception as e:
            print(f"Error writing updated content to {file_path}: {e}")
            # We continue with processed_content even if write failed,
            # so the parser sees the IDs.

    return nodes, processed_content
