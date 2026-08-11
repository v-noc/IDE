from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


NodeType = Literal["folder", "file", "class", "function", "call", "project"]
VisitMode = Literal["full", "contextual"]
SessionStatus = Literal["generating", "complete", "error", "aborted"]

SCHEMA_VERSION = "2"
PROMPT_VERSION = "5"


class RunRequest(BaseModel):
    project_id: str
    node_id: str
    depth: int = Field(ge=0, le=5)
    user_query: str = ""
    verbosity: Literal["quick", "normal", "detailed"] = "normal"


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
    truncated: bool = False


class EstimateResponse(Estimate):
    visit_list: VisitList


class PlannedBlock(BaseModel):
    start_line: int
    end_line: int
    focus: str = Field(
        max_length=100,
        description=(
            "User-facing label of what this block DOES, e.g. "
            "'validate the card fields'. At most 100 characters."
        ),
    )
    description: str = Field(
        description=(
            "One complete sentence to the narrator who will explain this block: "
            "what it does and why the code needs it."
        ),
    )


class BlockPlan(BaseModel):
    reasoning: str = Field(
        description=(
            "Think in order: (a) the code's overall structure, (b) where the "
            "natural seams are, (c) how many blocks that gives and why."
        ),
    )
    block_count: int = Field(
        description=(
            "The number of blocks your reasoning justified. "
            "blocks must contain exactly this many entries."
        ),
    )
    blocks: list[PlannedBlock]


class IntroOut(BaseModel):
    reasoning: str
    intro: str


class BlockTextOut(BaseModel):
    text: str


class BlockStep(BaseModel):
    index: int
    start_line: int
    end_line: int
    focus: str
    description: str = ""
    text: str = ""
    degraded: bool = False


class NodeSteps(BaseModel):
    node_id: str
    order: int
    mode: VisitMode
    intro_text: str = ""
    degraded: bool = False
    blocks: list[BlockStep] = Field(default_factory=list)


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0


class WalkthroughSession(BaseModel):
    id: str
    created_at: str
    request: RunRequest
    branch: str
    commit_id: str
    visit_list: VisitList
    node_steps: list[NodeSteps] = Field(default_factory=list)
    status: SessionStatus = "generating"
    error_log: list[str] = Field(default_factory=list)
    schema_version: str = SCHEMA_VERSION
    prompt_version: str = PROMPT_VERSION
    model_id: str
    usage: TokenUsage = Field(default_factory=TokenUsage)


def new_session(
    request: RunRequest,
    visit_list: VisitList,
    *,
    branch: str,
    commit_id: str,
    model_id: str,
) -> WalkthroughSession:
    return WalkthroughSession(
        id=str(uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        request=request,
        branch=branch,
        commit_id=commit_id,
        visit_list=visit_list,
        model_id=model_id,
        prompt_version=PROMPT_VERSION,
    )
