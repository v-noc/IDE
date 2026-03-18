from app.agent.graph.state import AgentState


def after_planner(state: AgentState) -> str:
    if state["should_finish"]:
        return "end"
    if state["selected_tool"]:
        return "executor"
    return "responder"


def after_reflector(state: AgentState) -> str:
    if state["should_finish"] or state["iteration_count"] >= state["max_iterations"]:
        return "responder"
    return "planner"
