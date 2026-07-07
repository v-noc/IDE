from __future__ import annotations

from typing import Any

from app.core.repository import Repositories
from app.core.repository.utils.child_raw import parse_code_element_child
from app.walkthrough.graph import GraphNode, build_graph


async def _fetch_node(repos: Repositories, node_id: str) -> Any | None:
    if node_id.startswith("CallSchema"):
        return await repos.call_repo.get_by_id(node_id)
    if node_id.startswith(("FolderSchema", "FileSchema", "ProjectSchema")) or "GroupSchema" in node_id:
        return await repos.structure_repo.get_by_id(node_id)
    return await repos.code_element_repo.get_by_id(node_id)


async def load_traversal_graph(
    repos: Repositories,
    start_node_id: str,
) -> dict[str, GraphNode]:
    """Load the subgraph reachable from ``start_node_id`` for traversal."""
    collected: dict[str, Any] = {}
    pending: list[str] = [start_node_id]
    seen: set[str] = set()

    while pending:
        node_id = pending.pop()
        if node_id in seen:
            continue
        seen.add(node_id)

        node = await _fetch_node(repos, node_id)
        if node is None:
            continue
        collected[node_id] = node

        descendants, target_lookup = (
            await repos.code_element_repo.get_code_descendant_nodes(
                node_id,
                child_types=[],
                depth_max=None,
            )
        )
        for desc in descendants:
            if desc and getattr(desc, "id", None):
                collected[str(desc.id)] = desc

        for raw in (target_lookup or {}).values():
            parsed = parse_code_element_child(raw)
            if parsed and getattr(parsed, "id", None):
                collected[str(parsed.id)] = parsed

        if node_id.startswith(("FolderSchema", "FileSchema", "ProjectSchema")):
            structure_children = await repos.structure_repo.get_children(
                node_id,
                exclude_types=[],
            )
            children_list = (
                structure_children[0]
                if isinstance(structure_children, tuple)
                else structure_children
            )
            for child in children_list or []:
                if child and getattr(child, "id", None):
                    collected[str(child.id)] = child

        for child_id in getattr(node, "children", set()) or set():
            pending.append(str(child_id))

    return build_graph(start_node_id, list(collected.values()))
