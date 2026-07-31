from __future__ import annotations

from pydantic import BaseModel, Field


class Scope(BaseModel):
    """How far to walk in one direction."""

    levels: int = 0
    all: bool = False


class Include(BaseModel):
    """What to render for nodes at some position."""

    description: bool = True
    docs: bool = False
    code: bool = False


class Caps(BaseModel):
    siblings: int = 10
    children_per_level: int = 20
    max_nodes: int = 60
    doc_tokens: int = 600
    code_lines_full: int = 80
    code_lines_head: int = 60


class ContextSpec(BaseModel):
    parent: Scope = Field(default_factory=Scope)
    children: Scope = Field(default_factory=Scope)
    siblings: bool = False
    self_include: Include = Field(default_factory=Include)
    parent_include: Include = Field(default_factory=Include)
    children_include: Include = Field(default_factory=Include)
    caps: Caps = Field(default_factory=Caps)


PRESETS: dict[str, ContextSpec] = {
    "project_header": ContextSpec(
        children=Scope(levels=1),
        children_include=Include(description=True),
    ),
    "attached_node": ContextSpec(
        parent=Scope(levels=1),
        siblings=True,
        children=Scope(levels=1),
        self_include=Include(description=True, docs=True, code=True),
        parent_include=Include(description=True),
        children_include=Include(description=True),
    ),
}


def get_preset(name: str) -> ContextSpec:
    if name not in PRESETS:
        raise KeyError(f"Unknown context preset: {name}")
    return PRESETS[name]
