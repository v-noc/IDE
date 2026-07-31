from __future__ import annotations

from dataclasses import dataclass, field
from xml.sax.saxutils import escape


@dataclass
class NodeCard:
    id: str
    kind: str
    name: str
    description: str = ""
    path: str | None = None
    lines: str | None = None
    qname: str | None = None


@dataclass
class ShapedNode:
    card: NodeCard
    description: str = ""
    parent: NodeCard | None = None
    siblings: list[NodeCard] = field(default_factory=list)
    children: list[NodeCard] = field(default_factory=list)
    docs: list[tuple[str, str]] = field(default_factory=list)
    code: str | None = None
    siblings_more: int = 0
    children_more: int = 0


def _attrs(card: NodeCard, *, include_id: bool = True) -> str:
    parts: list[str] = []
    if include_id:
        parts.append(f'id="{escape(card.id)}"')
    parts.append(f'kind="{escape(card.kind)}"')
    parts.append(f'name="{escape(card.name)}"')
    if card.path:
        parts.append(f'path="{escape(card.path)}"')
    if card.lines:
        parts.append(f'lines="{escape(card.lines)}"')
    return " ".join(parts)


def render_node_card(card: NodeCard) -> str:
    desc = (card.description or "").strip()
    if desc:
        return f"<node {_attrs(card, include_id=False)}>{escape(desc)}</node>"
    return f"<node {_attrs(card, include_id=False)}/>"


def render_project_header(name: str, description: str) -> str:
    body = escape((description or "").strip())
    return f'<project name="{escape(name)}">\n{body}\n</project>'


def render_attached_node(shaped: ShapedNode) -> str:
    lines: list[str] = [f"<attached_node {_attrs(shaped.card)}>"]
    desc = (shaped.description or shaped.card.description or "").strip()
    if desc:
        lines.append(f"  <description>{escape(desc)}</description>")
    if shaped.parent is not None:
        p = shaped.parent
        pdesc = escape((p.description or "").strip())
        if pdesc:
            lines.append(
                f'  <parent kind="{escape(p.kind)}" name="{escape(p.name)}">'
                f"{pdesc}</parent>",
            )
        else:
            lines.append(
                f'  <parent kind="{escape(p.kind)}" name="{escape(p.name)}"/>',
            )
    if shaped.siblings:
        lines.append("  <siblings>")
        for sib in shaped.siblings:
            lines.append(f"    {render_node_card(sib)}")
        if shaped.siblings_more:
            lines.append(f"    <more count=\"{shaped.siblings_more}\"/>")
        lines.append("  </siblings>")
    if shaped.children:
        lines.append("  <children>")
        for child in shaped.children:
            lines.append(f"    {render_node_card(child)}")
        if shaped.children_more:
            lines.append(f"    <more count=\"{shaped.children_more}\"/>")
        lines.append("  </children>")
    for title, body in shaped.docs:
        lines.append(
            f'  <doc title="{escape(title)}">{escape(body)}</doc>',
        )
    if shaped.code:
        line_attr = f' lines="{escape(shaped.card.lines)}"' if shaped.card.lines else ""
        lines.append(f"  <code{line_attr}>")
        lines.append(shaped.code)
        lines.append("  </code>")
    lines.append("</attached_node>")
    return "\n".join(lines)
