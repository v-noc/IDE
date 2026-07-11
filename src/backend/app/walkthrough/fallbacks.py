from __future__ import annotations

import math

from app.walkthrough.schemas import BlockPlan, PlannedBlock, VisitNode


def even_split_plan(
    start_line: int,
    end_line: int,
    *,
    min_blocks: int = 2,
    max_blocks: int = 6,
) -> BlockPlan:
    line_count = max(1, end_line - start_line + 1)
    count = max(min_blocks, min(max_blocks, math.ceil(line_count / 15)))
    size = max(1, math.ceil(line_count / count))

    blocks: list[PlannedBlock] = []
    cursor = start_line
    while cursor <= end_line and len(blocks) < count:
        block_end = min(end_line, cursor + size - 1)
        focus = f"lines {cursor}–{block_end}"
        blocks.append(
            PlannedBlock(
                start_line=cursor,
                end_line=block_end,
                focus=focus,
                description="",
            ),
        )
        cursor = block_end + 1

    if not blocks:
        focus = f"lines {start_line}–{end_line}"
        blocks = [
            PlannedBlock(
                start_line=start_line,
                end_line=end_line,
                focus=focus,
                description="",
            ),
        ]

    return BlockPlan(
        reasoning="Fallback even split after planner failure.",
        block_count=len(blocks),
        blocks=blocks,
    )


def single_block_plan(visit: VisitNode) -> BlockPlan:
    start = visit.start_line or 1
    end = visit.end_line or start
    return BlockPlan(
        reasoning="Whole body fits in one block.",
        block_count=1,
        blocks=[
            PlannedBlock(
                start_line=start,
                end_line=end,
                focus=visit.name,
                description="",
            ),
        ],
    )


def intro_fallback(visit: VisitNode) -> str:
    if visit.description.strip():
        return visit.description.strip()
    return f"{visit.name} ({visit.node_type})."


def block_text_fallback(focus: str) -> str:
    return focus
