from __future__ import annotations

import hashlib
import math
import re
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class FakeLLM:
    """Deterministic LLM for tests and offline development."""

    def __init__(
        self,
        call_type: str,
        *,
        fail_first_attempts: int = 0,
        malformed: bool = False,
    ):
        self.call_type = call_type
        self.fail_first_attempts = fail_first_attempts
        self.malformed = malformed
        self._attempts = 0

    async def invoke_structured(
        self,
        schema: type[T],
        system: str,
        user: str,
    ) -> T:
        self._attempts += 1

        if self.malformed and self._attempts <= self.fail_first_attempts:
            raise ValueError("fake malformed response")

        if self._attempts <= self.fail_first_attempts:
            raise ValueError("fake first attempt failure")

        name = _extract_node_name(user)

        if self.call_type == "intro":
            from app.walkthrough.schemas import IntroOut

            return IntroOut(
                reasoning=f"Read {name} from the outside.",
                intro=(
                    f"This `{name}` handles part of the flow described in the tour."
                ),
            )  # type: ignore[return-value]

        if self.call_type == "block_plan":
            from app.walkthrough.schemas import BlockPlan, PlannedBlock

            bounds = _extract_bounds(user)
            start, end = _extract_line_range(user)
            min_blocks, max_blocks = bounds
            span = max_blocks - min_blocks + 1
            count = min_blocks + (_stable_hash(name) % span)
            if start is None or end is None:
                blocks = [
                    PlannedBlock(start_line=1, end_line=10, focus="overview"),
                ]
            else:
                blocks = _even_blocks(start, end, count)
            return BlockPlan(
                reasoning=f"Split {name} into {len(blocks)} logical blocks.",
                blocks=blocks,
            )  # type: ignore[return-value]

        if self.call_type == "block_text":
            from app.walkthrough.schemas import BlockTextOut

            focus = _extract_focus(user)
            if _is_first_block(user):
                text = _first_block_markdown_text(focus or name)
            else:
                text = (
                    f"Explains {focus or name}: what this section does "
                    "and why it matters."
                )
            return BlockTextOut(text=text)  # type: ignore[return-value]

        raise ValueError(f"Unknown fake call type: {self.call_type}")


def _stable_hash(name: str) -> int:
    return int(hashlib.md5(name.encode()).hexdigest(), 16)


def _extract_node_name(user: str) -> str:
    match = re.search(r"^### node\s*\n(.+)", user, re.MULTILINE)
    if not match:
        return "this node"
    header = match.group(1).strip()
    return header.split("—")[0].strip() or header


def _extract_bounds(user: str) -> tuple[int, int]:
    match = re.search(r"between (\d+) and (\d+) blocks", user)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 2, 4


def _extract_line_range(user: str) -> tuple[int | None, int | None]:
    match = re.search(r"lines (\d+)[–-](\d+)", user)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None


def _extract_focus(user: str) -> str | None:
    match = re.search(r"### this block\s*\n(.+)", user, re.MULTILINE)
    return match.group(1).strip() if match else None


def _is_first_block(user: str) -> bool:
    return "### previous blocks" not in user


def _first_block_markdown_text(focus: str) -> str:
    long_narration = (
        "This section walks through validation, retries, and how errors "
        "propagate through the call stack when inputs are incomplete or "
        "external services are unavailable during processing. "
    ) * 6
    return (
        f"The block starts by validating input:\n\n"
        "```python\n"
        "if not card.valid():\n"
        "    raise PaymentError()\n"
        "```\n\n"
        f"Then it proceeds. {long_narration[:820]}"
    )


def _even_blocks(start: int, end: int, count: int) -> list:
    from app.walkthrough.schemas import PlannedBlock

    total = end - start + 1
    size = max(1, math.ceil(total / count))
    blocks = []
    cursor = start
    for _ in range(count):
        if cursor > end:
            break
        block_end = min(end, cursor + size - 1)
        blocks.append(
            PlannedBlock(
                start_line=cursor,
                end_line=block_end,
                focus=f"lines {cursor}–{block_end}",
            ),
        )
        cursor = block_end + 1
    return blocks or [PlannedBlock(start_line=start, end_line=end, focus=f"lines {start}–{end}")]
