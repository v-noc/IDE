from functools import lru_cache
from typing import List, Optional

from vnoc_lsp_python.id_injector import inject_ids
from vnoc_lsp_python.models import BaseNode
from vnoc_lsp_python.parser import JediParser


@lru_cache(maxsize=50)
def _inner_scan(content: str):
    processed_content, modified = inject_ids(content)
    parser = JediParser(processed_content)
    nodes = parser.parse()
    return nodes, processed_content, modified


def scan_with_meta(
    content: str, file_path: Optional[str] = None
) -> tuple[List[BaseNode], str, bool]:
    nodes, processed_content, modified = _inner_scan(content)

    if modified and file_path:
        try:
            with open(file_path, "w") as f:
                f.write(processed_content)
        except Exception as e:
            print(f"Error writing updated content to {file_path}: {e}")

    return nodes, processed_content, modified
