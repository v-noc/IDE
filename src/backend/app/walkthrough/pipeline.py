from __future__ import annotations

from app.core.services.code_element_service import CodeElementService
from app.walkthrough.context import NodeContext
from app.walkthrough.patcher import Patcher
from app.walkthrough.schemas import VisitNode, WalkthroughSession


async def _record_errors(
    patcher: Patcher,
    error_log: list[str],
    errors: list[str],
) -> None:
    if not errors:
        return
    error_log.extend(errors)
    for message in errors:
        await patcher.append_error(message)


def _numbered_code(code: str, start_line: int) -> str:
    lines = code.splitlines()
    parts = []
    for index, line in enumerate(lines):
        line_no = start_line + index
        parts.append(f"{line_no:4d} | {line}")
    return "\n".join(parts)


async def _load_numbered_code(
    code_service: CodeElementService,
    visit: VisitNode,
) -> str | None:
    if not visit.has_code or visit.start_line is None:
        return None
    code_node_id = (
        visit.target_id
        if visit.node_type == "call" and visit.target_id
        else visit.node_id
    )
    payload = await code_service.get_code(code_node_id)
    if not payload or not payload.get("code"):
        return None
    return _numbered_code(payload["code"], visit.start_line)


async def run_pipeline(
    session: WalkthroughSession,
    patcher: Patcher,
    *,
    code_service: CodeElementService,
    contexts: dict[int, NodeContext],
) -> WalkthroughSession:
    visit_list = session.visit_list
    if not visit_list.nodes:
        session = patcher.mirror.model_copy(deep=True)
        session.error_log = list(session.error_log)
        return session

    from app.walkthrough.orchestrator import GRAPH, make_initial_state

    errors: list[str] = list(session.error_log)
    config = {
        "configurable": {
            "patcher": patcher,
            "code_service": code_service,
            "contexts": contexts,
            "visit_list": visit_list,
            "errors": errors,
            "verbosity": session.request.verbosity,
            "user_query": session.request.user_query,
        },
        "recursion_limit": len(visit_list.nodes) * 10 + 50,
        "run_name": f"walkthrough {visit_list.nodes[0].name}",
        "metadata": {
            "session_id": session.id,
            "project_id": session.request.project_id,
            "depth": session.request.depth,
            "verbosity": session.request.verbosity,
            "user_query": session.request.user_query,
            "model_id": session.model_id,
            "prompt_version": session.prompt_version,
            "schema_version": session.schema_version,
        },
    }
    await GRAPH.ainvoke(make_initial_state(len(visit_list.nodes)), config)

    session = patcher.mirror.model_copy(deep=True)
    session.error_log = errors
    return session
