# app/agent/workflows/traversal_helpers.py

from collections import deque
from typing import Any


def collect_levels(roots: list[Any]) -> list[list[Any]]:
    if not roots:
        return []
    levels: list[list[Any]] = []
    queue: deque[tuple[Any, int]] = deque()
    visited: set[str] = set()
    for root in roots:
        rid = getattr(root, "id", None)
        if rid and rid not in visited:
            visited.add(rid)
            queue.append((root, 0))
    while queue:
        node, depth = queue.popleft()
        while len(levels) <= depth:
            levels.append([])
        levels[depth].append(node)
        for child in getattr(node, "children", []) or []:
            cid = getattr(child, "id", None)
            if cid and cid not in visited:
                visited.add(cid)
                queue.append((child, depth + 1))
    return levels


def ordered_nodes(roots: list[Any], direction: str) -> list[Any]:
    levels = collect_levels(roots)
    if direction == "up":
        levels = list(reversed(levels))
    return [n for level in levels for n in level]
