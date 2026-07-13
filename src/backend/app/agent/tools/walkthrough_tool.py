from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.agent.schemas.parts import ArtifactRef, ToolEstimate
from app.agent.tools.base import ToolOutcome, ToolServices, ToolSpec, register_tool
from app.walkthrough.depth import subtree_max_depth
from app.walkthrough.service import WalkthroughService


HARD_MAX_DEPTH = 5


class WalkthroughArgs(BaseModel):
    node_id: str = Field(
        description=(
            "The attached node to tour from. Only use ids the user "
            "attached to this conversation."
        ),
    )
    depth: int = Field(
        1,
        ge=0,
        le=5,
        description=(
            "How many levels below the start node. Suggest from the "
            "user's wording; the user confirms before the tour runs."
        ),
    )
    user_query: str = Field(
        "",
        description=(
            "The user's goal, one plain sentence in their words. "
            "Empty if they expressed no angle."
        ),
    )
    verbosity: Literal["quick", "normal", "detailed"] = Field(
        "normal",
        description="Narration length: quick | normal | detailed.",
    )


class WalkthroughTool:
    async def estimate(
        self,
        args: WalkthroughArgs,
        services: ToolServices,
    ) -> ToolEstimate:
        uow = services.uow
        repos = uow.get_project_repos()
        subtree_max = await subtree_max_depth(
            repos, args.node_id, hard_cap=HARD_MAX_DEPTH,
        )
        depth = max(0, min(args.depth, subtree_max, HARD_MAX_DEPTH))

        service = WalkthroughService(uow)
        estimate = await service.estimate(args.node_id, depth)
        return ToolEstimate(
            items=estimate.node_count,
            llm_calls=estimate.llm_call_estimate,
            label=(
                f"{estimate.node_count} stops · "
                f"~{estimate.llm_call_estimate} LLM calls"
            ),
            over_cap=estimate.over_cap,
            knobs={
                "depth": {"value": depth, "max": subtree_max},
                "verbosity": args.verbosity,
            },
        )

    async def run(
        self,
        args: WalkthroughArgs,
        services: ToolServices,
    ) -> ToolOutcome:
        """Run the existing walkthrough pipeline into an artifact doc.

        Phase 3 ships estimate + a compact outcome. Full multi-doc patch
        bridging reuses WalkthroughService when emit/patcher are bound;
        otherwise returns a deferred/planned outcome for confirmation-only
        smoke paths.
        """
        uow = services.uow
        repos = uow.get_project_repos()
        subtree_max = await subtree_max_depth(
            repos, args.node_id, hard_cap=HARD_MAX_DEPTH,
        )
        depth = max(0, min(args.depth, subtree_max, HARD_MAX_DEPTH))

        service = WalkthroughService(uow)
        estimate = await service.estimate(args.node_id, depth)
        if estimate.over_cap:
            return ToolOutcome(
                result={
                    "status": "refused",
                    "reason": (
                        f"~{estimate.node_count} stops at depth {depth} "
                        "exceeds the visit cap — try a smaller depth."
                    ),
                    "node_count": estimate.node_count,
                },
                degraded=False,
            )

        session_id = f"walkthrough_session/{uuid.uuid4().hex[:12]}"

        # Full pipeline streaming when the harness bound an emit + patcher.
        if services.patcher is not None and services.emit is not None:
            outcome = await _run_pipeline_bridged(
                uow=uow,
                args=args.model_copy(update={"depth": depth}),
                session_id=session_id,
                patcher=services.patcher,
                emit=services.emit,
                estimate=estimate,
            )
            return outcome

        return ToolOutcome(
            result={
                "session_id": session_id,
                "status": "planned",
                "stops": estimate.node_count,
                "steps": estimate.step_estimate,
                "llm_calls": estimate.llm_call_estimate,
                "depth": depth,
                "user_query": args.user_query,
                "verbosity": args.verbosity,
                "degraded_count": 0,
            },
            artifact=ArtifactRef(doc=session_id, render="walkthrough"),
            degraded=False,
        )


async def _run_pipeline_bridged(
    *,
    uow: Any,
    args: WalkthroughArgs,
    session_id: str,
    patcher: Any,
    emit: Any,
    estimate: Any,
) -> ToolOutcome:
    """Bridge walkthrough Patcher frames onto the conversation multi-doc stream."""
    from app.core.services.code_element_service import CodeElementService
    from app.walkthrough.context import build_contexts
    from app.walkthrough.loader import load_traversal_graph
    from app.walkthrough.patcher import Patcher
    from app.walkthrough.pipeline import run_pipeline
    from app.walkthrough.schemas import RunRequest, new_session
    from app.walkthrough.traversal import build_visit_list

    project = uow.project
    repos = uow.get_project_repos()
    graph = await load_traversal_graph(repos, args.node_id)
    visit_list = build_visit_list(graph, args.node_id, args.depth)
    request = RunRequest(
        project_id=project.id,
        node_id=args.node_id,
        depth=args.depth,
    )
    session = new_session(
        request,
        visit_list,
        branch=getattr(uow.ctx, "branch", "main") or "main",
        commit_id="head",
        model_id="walkthrough",
    )
    # Stamp intent for evals (fields may be ignored if schema not yet extended)
    if hasattr(session, "model_copy"):
        try:
            session = session.model_copy(
                update={
                    "id": session_id.split("/", 1)[-1],
                },
            )
        except Exception:
            pass

    async def bridged_emit(frame: dict[str, Any]) -> None:
        kind = frame.get("kind")
        if kind == "hello":
            await patcher.open_doc(session_id, frame.get("session") or session)
            return
        if kind == "end":
            await patcher.close_doc(
                session_id,
                frame.get("status") or "complete",
                frame.get("message"),
            )
            return
        if kind == "patch":
            # Re-emit as multi-doc patch on the artifact doc
            from app.agent.harness.frames import patch_frame

            seq = frame.get("seq", 0)
            ops = frame.get("ops") or []
            await emit(patch_frame(session_id, seq, ops))
            return
        await emit({**frame, "doc": session_id})

    wt_patcher = Patcher(session, bridged_emit)
    hello = await wt_patcher.hello_frame()
    await bridged_emit(hello)

    contexts = await build_contexts(graph, visit_list, repos)
    code_service = CodeElementService(uow)
    try:
        await run_pipeline(
            session,
            wt_patcher,
            code_service=code_service,
            contexts=contexts,
        )
        status = "complete"
    except Exception as exc:
        await bridged_emit(
            {"kind": "end", "status": "error", "message": str(exc)},
        )
        return ToolOutcome(
            result={
                "session_id": session_id,
                "status": "error",
                "error": str(exc),
                "stops": estimate.node_count,
            },
            artifact=ArtifactRef(doc=session_id, render="walkthrough"),
            degraded=True,
        )

    degraded_count = sum(
        1 for step in wt_patcher.mirror.node_steps if getattr(step, "degraded", False)
    )
    await bridged_emit({"kind": "end", "status": status})
    return ToolOutcome(
        result={
            "session_id": session_id,
            "status": status,
            "stops": len(wt_patcher.mirror.node_steps),
            "steps": estimate.step_estimate,
            "llm_calls": estimate.llm_call_estimate,
            "depth": args.depth,
            "user_query": args.user_query,
            "verbosity": args.verbosity,
            "degraded_count": degraded_count,
        },
        artifact=ArtifactRef(doc=session_id, render="walkthrough"),
        degraded=bool(degraded_count),
    )


WALKTHROUGH_SPEC = ToolSpec(
    name="walkthrough",
    description=(
        "Generate a guided, step-by-step tour of a code node the user "
        "attached. Streams a playable walkthrough; the user sees it as a "
        "tour outline. Costs LLM calls — an estimate is shown for approval."
    ),
    input_model=WalkthroughArgs,
    kind="task",
    confirmation="over_threshold",
    render="walkthrough",
    handler=WalkthroughTool(),
)

register_tool(WALKTHROUGH_SPEC)
