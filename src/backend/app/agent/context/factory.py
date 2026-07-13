from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.agent.context.loader import (
    load_docs_excerpt,
    load_neighborhood,
    number_code,
    trim_code,
)
from app.agent.context.specs import ContextSpec, get_preset
from app.agent.context.xml import (
    NodeCard,
    ShapedNode,
    render_attached_node,
    render_project_header,
)
from app.core.repository import Repositories
from app.walkthrough.graph import (
    GraphNode,
    expand_children_with_groups,
    sort_children_by_source,
)

CodeLoader = Callable[[str], Awaitable[str | None]]


def _card(node: GraphNode) -> NodeCard:
    lines = None
    if node.line_no is not None and node.end_line_no is not None:
        lines = f"{node.line_no}-{node.end_line_no}"
    return NodeCard(
        id=node.id,
        kind=node.kind,
        name=node.name,
        description=node.description or "",
        qname=node.qname,
        lines=lines,
    )


def shape_attached_node(
    graph: dict[str, GraphNode],
    node_id: str,
    spec: ContextSpec,
    *,
    docs: list[tuple[str, str]] | None = None,
    code: str | None = None,
) -> ShapedNode | None:
    node = graph.get(node_id)
    if node is None:
        return None

    shaped = ShapedNode(card=_card(node))
    if spec.self_include.description:
        shaped.description = (node.description or "").strip()

    if spec.parent.levels >= 1 and node.parent_id:
        parent = graph.get(node.parent_id)
        if parent is not None:
            shaped.parent = _card(parent)

    if spec.siblings and node.parent_id:
        parent = graph.get(node.parent_id)
        if parent is not None:
            sibs: list[NodeCard] = []
            for child_id in parent.children:
                if child_id == node_id:
                    continue
                child = graph.get(child_id)
                if child is None or child.kind == "group":
                    continue
                if not (child.description or "").strip():
                    continue
                sibs.append(_card(child))
            cap = spec.caps.siblings
            if len(sibs) > cap:
                shaped.siblings_more = len(sibs) - cap
                sibs = sibs[:cap]
            shaped.siblings = sibs

    if spec.children.levels >= 1:
        pairs = expand_children_with_groups(graph, node_id)
        child_ids = [cid for cid, _ in pairs]
        ordered = sort_children_by_source(graph, child_ids)
        kids: list[NodeCard] = []
        for cid in ordered:
            child = graph.get(cid)
            if child is None:
                continue
            if spec.children_include.description and not (
                child.description or ""
            ).strip():
                continue
            kids.append(_card(child))
        cap = spec.caps.children_per_level
        if len(kids) > cap:
            shaped.children_more = len(kids) - cap
            kids = kids[:cap]
        shaped.children = kids

    if spec.self_include.docs and docs:
        # rough token ≈ chars/4; cap by doc_tokens * 4 chars
        char_budget = spec.caps.doc_tokens * 4
        kept: list[tuple[str, str]] = []
        used = 0
        for title, body in docs:
            if used >= char_budget:
                break
            chunk = body[: max(0, char_budget - used)]
            kept.append((title, chunk))
            used += len(chunk)
        shaped.docs = kept

    if spec.self_include.code and code:
        end = node.end_line_no or 1
        start = node.line_no or 1
        numbered = number_code(code, start)
        shaped.code = trim_code(
            numbered,
            end,
            full_max=spec.caps.code_lines_full,
            head=spec.caps.code_lines_head,
        )

    return shaped


class ContextFactory:
    def __init__(
        self,
        repos: Repositories,
        *,
        code_loader: CodeLoader | None = None,
    ):
        self.repos = repos
        self.code_loader = code_loader

    async def build(
        self,
        node_id: str,
        spec: ContextSpec,
        *,
        include_code: bool = True,
    ) -> str:
        parent_levels = spec.parent.levels if not spec.parent.all else 8
        children_levels = spec.children.levels if not spec.children.all else 3
        graph = await load_neighborhood(
            self.repos,
            node_id,
            parent_levels=parent_levels,
            children_levels=children_levels,
            include_siblings=spec.siblings,
        )
        if node_id not in graph:
            return f'<attached_node id="{node_id}" kind="unknown" name="?"/>'

        docs: list[tuple[str, str]] = []
        node = graph[node_id]
        if spec.self_include.docs and node.documents:
            docs = await load_docs_excerpt(
                self.repos,
                list(node.documents),
                char_cap=spec.caps.doc_tokens * 4,
            )

        code: str | None = None
        if include_code and spec.self_include.code and self.code_loader:
            if node.kind in ("function", "class", "file"):
                code = await self.code_loader(node_id)

        shaped = shape_attached_node(
            graph, node_id, spec, docs=docs, code=code,
        )
        if shaped is None:
            return f'<attached_node id="{node_id}" kind="unknown" name="?"/>'
        return render_attached_node(shaped)

    async def build_preset(
        self,
        node_id: str,
        preset: str,
        *,
        include_code: bool = True,
    ) -> str:
        return await self.build(
            node_id, get_preset(preset), include_code=include_code,
        )

    def project_header(self, name: str, description: str) -> str:
        return render_project_header(name, description)
