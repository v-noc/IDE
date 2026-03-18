from typing import TypedDict, Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ToolResult(TypedDict):
    tool_name: str
    tool_input: dict
    output: str  # serialized result
    error: Optional[str]


class AgentState(TypedDict):
    """Shared state flowing through the LangGraph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Planning
    plan: Optional[str]                  # high-level plan text
    current_step: int                    # index in plan steps

    # Tool execution
    selected_tool: Optional[str]
    tool_input: Optional[dict]
    tool_results: list[ToolResult]

    # Context
    # retrieved graph nodes / vector results
    context_docs: list[dict]
    token_budget_remaining: int

    # Control
    iteration_count: int
    max_iterations: int
    should_finish: bool

    # Workflow-specific (used by subgraphs)
    target_node_id: Optional[str]        # node being documented
    traversal_direction: Optional[str]   # "up" | "down"
    # "description" | "documentation" | "both"
    generation_mode: Optional[str]
