from typing import List, Optional
from .models import BaseNode
from .parser import JediParser
from .id_injector import inject_ids
import os

def scan(content: str, file_path: Optional[str] = None) -> List[BaseNode]:
    """
    Scans the content, injects IDs if missing (and updates file), and returns the parsed AST.
    """
    # Step 1: Inject IDs
    # We only write to file if file_path is provided AND content was modified.
    processed_content, modified = inject_ids(content)
    
    if modified and file_path:
        try:
            with open(file_path, "w") as f:
                f.write(processed_content)
        except Exception as e:
            print(f"Error writing updated content to {file_path}: {e}")
            # We continue with processed_content even if write failed, 
            # so the parser sees the IDs.

    # Step 2: Parse with Jedi/Parso
    parser = JediParser(processed_content)
    return parser.parse()
