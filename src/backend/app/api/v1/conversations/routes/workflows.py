"""Background agent workflows (mounted under /api/v1/agent)."""

from __future__ import annotations

from typing import Any, Optional, Type

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agent.context.graph_traversal import GraphTraversal
from app.agent.conversation_store import ConversationStore
from app.agent.service.workflow_service import WorkflowService
from app.agent.workflows.base import BaseWorkflow
from app.agent.workflows.description_gen import DescriptionGeneratorWorkflow
from app.agent.workflows.documentation_gen import DocumentationGeneratorWorkflow
from app.api.dependencies import (
    get_project_conversation_store,
    get_workflow_service,
)
from app.api.v1.conversations.deps import get_graph_traversal

router = APIRouter(prefix="/workflows", tags=["Agent Workflows"])

_WORKFLOW_CLASSES: dict[str, Type[BaseWorkflow]] = {
    "documentation_generator": DocumentationGeneratorWorkflow,
    "description_generator": DescriptionGeneratorWorkflow,
}


class RunWorkflowRequest(BaseModel):
    workflow_name: str
    params: dict[str, Any]
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None


class RunWorkflowResponse(BaseModel):
    conversation_id: str
    task_id: str
    status: str


@router.post("/run", response_model=RunWorkflowResponse, status_code=202)
async def run_workflow(
    req: RunWorkflowRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
    graph: GraphTraversal = Depends(get_graph_traversal),
    store: ConversationStore = Depends(get_project_conversation_store),
):
    """
    Trigger a background workflow (e.g., documentation generation).
    If conversation_id is None, a new conversation is automatically created.
    """
    workflow_cls = _WORKFLOW_CLASSES.get(req.workflow_name)
    if not workflow_cls:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown workflow: {req.workflow_name}",
        )

    workflow = workflow_cls(
        graph=graph,
        llm_factory=workflow_service.llm_factory,
    )

    try:
        params = dict(req.params or {})
        params.pop("mode", None)

        conv_id, task_id = await workflow_service.run(
            workflow,
            store=store,
            conversation_id=req.conversation_id,
            **params,
        )

        return RunWorkflowResponse(
            conversation_id=conv_id,
            task_id=task_id,
            status="accepted_and_running",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start workflow: {e}"
        ) from e
