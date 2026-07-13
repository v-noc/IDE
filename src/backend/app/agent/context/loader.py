from __future__ import annotations

from typing import Any

from app.core.repository import Repositories
from app.walkthrough.graph import GraphNode, build_graph
from app.walkthrough.loader import _fetch_node


async def fetch_node(repos: Repositories, node_id: str) -> Any | None:
    return await _fetch_node(repos, node_id)


async def load_neighborhood(
    repos: Repositories,
    node_id: str,
    *,
    parent_levels: int = 1,
    children_levels: int = 1,
    include_siblings: bool = True,
) -> dict[str, GraphNode]:
    """Load a small neighborhood around ``node_id`` as GraphNodes."""
    collected: dict[str, Any] = {}
    root = await fetch_node(repos, node_id)
    if root is None:
        return {}
    collected[node_id] = root

    # Ancestors via lineage query (root → leaf order typically)
    if parent_levels > 0 or include_siblings:
        try:
            lineage = await repos.code_element_repo.get_node_lineage(node_id)
        except Exception:
            lineage = []
        # lineage includes self + ancestors; keep closest parents
        for doc in lineage or []:
            if doc is None or not getattr(doc, "id", None):
                continue
            collected[str(doc.id)] = doc

    if children_levels >= 1:
        await _load_children(repos, collected, node_id, depth=children_levels)

    graph = build_graph(node_id, list(collected.values()))

    # Ensure siblings of the focus node are present when requested
    if include_siblings:
        focus = graph.get(node_id)
        if focus and focus.parent_id:
            parent = graph.get(focus.parent_id)
            if parent:
                for child_id in list(parent.children):
                    if child_id not in collected:
                        child = await fetch_node(repos, child_id)
                        if child is not None:
                            collected[child_id] = child
                graph = build_graph(node_id, list(collected.values()))

    return graph


async def _load_children(
    repos: Repositories,
    collected: dict[str, Any],
    node_id: str,
    *,
    depth: int,
) -> None:
    if depth < 1:
        return

    if node_id.startswith(("FolderSchema", "FileSchema", "ProjectSchema")):
        try:
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
                cid = str(getattr(child, "id", "") or "")
                if cid:
                    collected[cid] = child
                    if depth > 1:
                        await _load_children(
                            repos, collected, cid, depth=depth - 1,
                        )
        except Exception:
            pass
        return

    try:
        descendants, target_lookup = (
            await repos.code_element_repo.get_code_descendant_nodes(
                node_id,
                child_types=[],
                depth_max=depth,
            )
        )
        for desc in descendants or []:
            if desc and getattr(desc, "id", None):
                collected[str(desc.id)] = desc
        for raw in (target_lookup or {}).values():
            from app.core.repository.utils.child_raw import (
                parse_code_element_child,
            )

            parsed = parse_code_element_child(raw)
            if parsed and getattr(parsed, "id", None):
                collected[str(parsed.id)] = parsed
    except Exception:
        pass


async def load_docs_excerpt(
    repos: Repositories,
    document_ids: list[str],
    *,
    char_cap: int = 800,
    total_cap: int = 2400,
) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    total = 0
    for doc_id in document_ids[:3]:
        if total >= total_cap:
            break
        try:
            doc = await repos.document_repo.get_by_id(doc_id)
        except Exception:
            continue
        if doc is None:
            continue
        data = (getattr(doc, "data", "") or "").strip()
        if not data:
            continue
        if len(data) > char_cap:
            data = data[:char_cap].rstrip() + "[…]"
        title = getattr(doc, "name", "") or "doc"
        if total + len(data) > total_cap:
            data = data[: max(0, total_cap - total)].rstrip() + "[…]"
        out.append((title, data))
        total += len(data)
    return out


def trim_code(
    numbered: str,
    end_line: int,
    *,
    full_max: int = 80,
    head: int = 60,
) -> str:
    lines = numbered.splitlines()
    if len(lines) <= full_max:
        return numbered
    remaining = len(lines) - head
    marker = f"[… trimmed: {remaining} more lines, through line {end_line}]"
    return "\n".join([*lines[:head], marker])


def number_code(code: str, start_line: int = 1) -> str:
    lines = code.splitlines()
    return "\n".join(
        f"{start_line + i:>4} | {line}" for i, line in enumerate(lines)
    )
