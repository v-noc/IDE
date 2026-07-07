from __future__ import annotations

from fastapi import HTTPException, status

from app.db.context import ProjectUoW
from app.walkthrough.loader import load_traversal_graph
from app.walkthrough.schemas import Estimate, EstimateResponse, VisitList
from app.walkthrough.traversal import build_visit_list, compute_estimate


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
