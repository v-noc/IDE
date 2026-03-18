
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import planner, executor, reflector, responder
from .edges import after_planner, after_reflector


def build_agent_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner)
    graph.add_node("executor", executor)
    graph.add_node("reflector", reflector)
    graph.add_node("responder", responder)

    graph.set_entry_point("planner")

    graph.add_conditional_edges("planner", after_planner, {
        "executor": "executor",
        "responder": "responder",
        "end": END,
    })
    graph.add_edge("executor", "reflector")
    graph.add_conditional_edges("reflector", after_reflector, {
        "responder": "responder",
        "planner": "planner",
    })
    graph.add_edge("responder", END)

    return graph.compile()
