from app.agent.graph.state import AgentState


async def planner(state: AgentState) -> AgentState:
    """
    Given messages + context, produce a plan.
    Decides: use a tool, answer directly, or give up.
    Populates: plan, selected_tool, tool_input.
    """
    ...


async def executor(state: AgentState) -> AgentState:
    """
    Look up selected_tool in ToolRegistry, call execute().
    Populates: tool_results (appends).
    """
    ...


async def reflector(state: AgentState) -> AgentState:
    """
    Review tool results. Decide if we have enough context to answer,
    or if we need another tool call.
    Populates: should_finish, context_docs.
    """
    ...


async def responder(state: AgentState) -> AgentState:
    """
    Generate the final response from accumulated context.
    Appends an assistant message to messages.
    """
    ...
