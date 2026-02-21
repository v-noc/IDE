import os
import textwrap
from typing import Optional

import aiofiles

from app.core.model.properties import CodePosition


def build_abs_file_path(project_path: str, file_path: str) -> str:
    """Build absolute file path from project root and relative file path."""
    if os.path.isabs(file_path):
        return file_path
    return os.path.normpath(os.path.join(project_path, file_path))


async def extract_code_from_file(
    abs_path: str,
    position: Optional[CodePosition],
) -> str:
    """Read code once and optionally slice by line/column positions.

    - If position is None: returns the entire file content.
    - If position is provided: returns content from
      (line_no, col_offset) inclusive to (end_line_no, end_col_offset)
      exclusive. Indices follow the semantics used in CodePosition.
    """
    if position is None:
        async with aiofiles.open(abs_path, "r", encoding="utf-8") as f:
            return await f.read()

    start_line = max(1, position.line_no)
    end_line = position.end_line_no
    end_col = position.end_col_offset

    collected: list[str] = []
    async with aiofiles.open(abs_path, "r", encoding="utf-8") as f:
        idx = 1
        async for raw_line in f:
            if idx < start_line:
                idx += 1
                continue

            line = raw_line[:-1] if raw_line.endswith("\n") else raw_line

            if end_line is None or idx < end_line:
                collected.append(line)
            elif idx == end_line:
                slice_end = None if end_col is None else end_col
                collected.append(line[:slice_end])
                break
            else:
                break
            idx += 1

    if not collected:
        return ""

    joined = "\n".join(collected)
    return textwrap.dedent(joined)
