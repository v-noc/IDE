from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


NodeType = Literal["folder", "file", "class", "function", "call", "project"]
VisitMode = Literal["full", "contextual"]


class RunRequest(BaseModel):
    project_id: str
    node_id: str
    depth: int = Field(ge=0, le=3)


class Estimate(BaseModel):
    node_count: int
    step_estimate: int
    llm_call_estimate: int
    over_cap: bool


class VisitNode(BaseModel):
    node_id: str
    name: str
    qname: str | None
    node_type: NodeType
    description: str
    level: int
    order: int
    parent_order: int | None
    target_id: str | None
    mode: VisitMode
    first_seen_order: int | None
    has_code: bool
    start_line: int | None
    end_line: int | None
    line_count: int | None
    gated: bool


class VisitList(BaseModel):
    start_node_id: str
    depth: int
    nodes: list[VisitNode]


class EstimateResponse(Estimate):
    visit_list: VisitList
