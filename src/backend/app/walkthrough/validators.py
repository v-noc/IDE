from __future__ import annotations

from app.walkthrough.schemas import BlockPlan, VisitNode


def validate_block_plan(plan: BlockPlan, visit: VisitNode) -> list[str]:
    errors: list[str] = []
    if visit.start_line is None or visit.end_line is None:
        return errors

    start = visit.start_line
    end = visit.end_line
    min_blocks, max_blocks = _bounds(visit.line_count)

    if not (min_blocks <= len(plan.blocks) <= max_blocks):
        errors.append(
            f"expected {min_blocks}–{max_blocks} blocks, got {len(plan.blocks)}",
        )

    covered = set()
    last_start = start - 1
    for block in sorted(plan.blocks, key=lambda b: b.start_line):
        if block.start_line < start or block.end_line > end:
            errors.append(
                f"block {block.start_line}-{block.end_line} outside [{start}, {end}]",
            )
        if block.start_line <= last_start:
            errors.append("blocks must be ordered and non-overlapping")
        if block.end_line < block.start_line:
            errors.append("block end_line before start_line")
        last_start = block.start_line
        covered.update(range(block.start_line, block.end_line + 1))

    total_lines = end - start + 1
    if total_lines > 0 and len(covered) / total_lines < 0.8:
        errors.append("blocks must cover at least 80% of the node's lines")

    return errors


def _bounds(line_count: int | None) -> tuple[int, int]:
    lines = line_count or 0
    max_blocks = max(2, min(6, lines // 5)) if lines else 2
    return 2, max_blocks
