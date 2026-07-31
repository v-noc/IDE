from __future__ import annotations

from app.walkthrough.graph import GraphNode
from app.walkthrough.loader import load_traversal_graph
from app.core.repository import Repositories


async def subtree_max_depth(
    repos: Repositories,
    node_id: str,
    *,
    hard_cap: int = 5,
) -> int:
    """Real max depth of the subtree, capped at ``hard_cap``.

    Uses a bounded load + BFS levels (correct fallback when WOQL
    ``{n,m}`` path probes are unavailable).
    """
    graph = await load_traversal_graph(repos, node_id, depth_max=hard_cap)
    if node_id not in graph:
        return 0

    # BFS levels from the start node
    level = {node_id: 0}
    queue = [node_id]
    max_level = 0
    while queue:
        current = queue.pop(0)
        current_level = level[current]
        if current_level >= hard_cap:
            continue
        node = graph.get(current)
        if node is None:
            continue
        for child_id in _expanded_children(graph, current):
            if child_id in level:
                continue
            level[child_id] = current_level + 1
            max_level = max(max_level, current_level + 1)
            queue.append(child_id)
    return min(max_level, hard_cap)


def _expanded_children(graph: dict[str, GraphNode], node_id: str) -> list[str]:
    from app.walkthrough.graph import expand_children

    return expand_children(graph, node_id)
