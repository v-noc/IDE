from __future__ import annotations

import asyncio
from typing import Any

from fastapi import HTTPException, status
from loguru import logger

from app.agent.llm.providers import resolve_model_id
from app.agent.llm.structured import make_llm
from app.core.services.code_element_service import CodeElementService
from app.db.context import ProjectUoW
from app.walkthrough.context import build_contexts
from app.walkthrough.loader import load_traversal_graph
from app.walkthrough.patcher import Patcher
from app.walkthrough.pipeline import run_pipeline
from app.walkthrough.schemas import (
    EstimateResponse,
    RunRequest,
    VisitList,
    WalkthroughSession,
    new_session,
)
from app.walkthrough.traversal import VISIT_CAP, build_visit_list, compute_estimate
from app.walkthrough.transport import ndjson_response

_active_runs: dict[str, str] = {}


class WalkthroughService:
    def __init__(self, uow: ProjectUoW):
        self.uow = uow

    async def estimate(self, node_id: str, depth: int) -> EstimateResponse:
        repos = self.uow.get_project_repos()
        graph = await load_traversal_graph(repos, node_id)

        if node_id not in graph:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node not found: {node_id}",
            )

        visit_list = build_visit_list(graph, node_id, depth)
        estimate = compute_estimate(visit_list)

        return EstimateResponse(
            **estimate.model_dump(),
            visit_list=visit_list,
        )

    async def build_visit_list_only(self, node_id: str, depth: int) -> VisitList:
        repos = self.uow.get_project_repos()
        graph = await load_traversal_graph(repos, node_id)
        return build_visit_list(graph, node_id, depth)

    def run(self, request: RunRequest, code_service: CodeElementService):
        project_id = request.project_id
        if project_id in _active_runs:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "A walkthrough is already running for this project.",
                    "session_id": _active_runs[project_id],
                },
            )

        placeholder_id = f"pending-{project_id}"
        _active_runs[project_id] = placeholder_id

        return ndjson_response(lambda: self._stream_run(request, code_service))

    async def _stream_run(
        self,
        request: RunRequest,
        code_service: CodeElementService,
    ):
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        project_id = request.project_id

        async def emit(frame: dict[str, Any]) -> None:
            await queue.put(frame)

        async def producer() -> None:
            session: WalkthroughSession | None = None
            try:
                try:
                    make_llm("intro")
                except Exception as exc:
                    await queue.put(
                        {
                            "kind": "end",
                            "status": "error",
                            "message": f"LLM provider not configured: {exc}",
                        },
                    )
                    return

                repos = self.uow.get_project_repos()
                graph = await load_traversal_graph(repos, request.node_id)
                if request.node_id not in graph:
                    await queue.put(
                        {
                            "kind": "end",
                            "status": "error",
                            "message": f"Node not found: {request.node_id}",
                        },
                    )
                    return

                visit_list = build_visit_list(graph, request.node_id, request.depth)
                estimate = compute_estimate(visit_list)
                if estimate.over_cap:
                    await queue.put(
                        {
                            "kind": "end",
                            "status": "error",
                            "message": (
                                f"Visit list exceeds cap ({VISIT_CAP} stops). "
                                "Lower the depth."
                            ),
                        },
                    )
                    return

                contexts = await build_contexts(graph, visit_list, repos)

                branch = self.uow.ctx.branch
                commit_id = self.uow.ctx.ref or f"{branch}@head"
                session = new_session(
                    request,
                    visit_list,
                    branch=branch,
                    commit_id=commit_id,
                    model_id=resolve_model_id(),
                )

                _active_runs[project_id] = session.id
                patcher = Patcher(session, emit)
                await queue.put(await patcher.hello_frame())

                # Connection stays open (NDJSON) while the pipeline finishes each
                # stop. Token-level streaming can land later; today each step's
                # finished text is patched as soon as the structured call returns.
                final_session = await run_pipeline(
                    session,
                    patcher,
                    code_service=code_service,
                    contexts=contexts,
                )
                await patcher.set_status("complete")
                await queue.put(await patcher.end_frame("complete"))

                degraded_count = sum(
                    1
                    for node_steps in final_session.node_steps
                    if node_steps.degraded
                    or any(block.degraded for block in node_steps.blocks)
                )
                logger.info(
                    "walkthrough complete id={} stops={} degraded={} errors={}",
                    final_session.id,
                    len(final_session.node_steps),
                    degraded_count,
                    len(final_session.error_log),
                )
                # TODO(persistence): save final_session
            except asyncio.CancelledError:
                if session is not None:
                    patcher = Patcher(session, emit)
                    await patcher.set_status("aborted")
                raise
            except Exception as exc:
                await queue.put(
                    {"kind": "end", "status": "error", "message": str(exc)},
                )
            finally:
                _active_runs.pop(project_id, None)
                await queue.put(None)

        task = asyncio.create_task(producer())
        try:
            while True:
                frame = await queue.get()
                if frame is None:
                    break
                yield frame
        finally:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
