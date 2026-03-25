# app/api/v1/agent/workflows/router.py

from __future__ import annotations

from typing import Any, Optional, Type

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agent.context.graph_traversal import GraphTraversal
from app.agent.conversation_store import ConversationStore
from app.agent.service.workflow_service import WorkflowService
from app.agent.workflows.base import BaseWorkflow
from app.agent.workflows.description_gen import (
    DescriptionGeneratorWorkflow,
)
from app.agent.workflows.documentation_gen import (
    DocumentationGeneratorWorkflow,
)
from app.api.dependencies import (
    get_project_conversation_store,
    get_workflow_service,
)
from app.api.v1.conversations.deps import get_graph_traversal

router = APIRouter(
    prefix="/workflows", tags=["Agent Workflows"]
)

_WORKFLOW_CLASSES: dict[str, Type[BaseWorkflow]] = {
    "documentation_generator": DocumentationGeneratorWorkflow,
    "description_generator": DescriptionGeneratorWorkflow,
}


class RunWorkflowRequest(BaseModel):
    workflow_name: str
    params: dict[str, Any]
    conversation_id: Optional[str] = None
    # Persisted on the Task row (display name / notes), not the conversation thread.
    conversation_title: Optional[str] = None
    conversation_description: Optional[str] = None


class RunWorkflowResponse(BaseModel):
    conversation_id: str
    task_id: str
    status: str


class WorkflowBatchStep(BaseModel):
    workflow_name: str
    params: dict[str, Any]


class RunWorkflowBatchRequest(BaseModel):
    steps: list[WorkflowBatchStep]
    conversation_id: Optional[str] = None
    # Labels the batch parent Task; chat title/description are always LLM-generated.
    conversation_title: Optional[str] = None
    conversation_description: Optional[str] = None


class RunWorkflowBatchResponse(BaseModel):
    conversation_id: str
    task_id: str  # single parent task
    status: str


@router.post(
    "/run",
    response_model=RunWorkflowResponse,
    status_code=202,
)
async def run_workflow(
    req: RunWorkflowRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
    graph: GraphTraversal = Depends(get_graph_traversal),
    store: ConversationStore = Depends(get_project_conversation_store),
):
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
        # Remove mode if present (legacy cleanup)
        params.pop("mode", None)

        if req.conversation_title is not None:
            params["conversation_title"] = req.conversation_title
        if req.conversation_description is not None:
            params["conversation_description"] = req.conversation_description

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
        # logger.exception("Workflow run failed")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start workflow: {e}",
        ) from e


@router.post(
    "/run-batch",
    response_model=RunWorkflowBatchResponse,
    status_code=202,
)
async def run_workflow_batch(
    req: RunWorkflowBatchRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
    graph: GraphTraversal = Depends(get_graph_traversal),
    store: ConversationStore = Depends(get_project_conversation_store),
):
    """
    Run multiple workflows sequentially as a single background task.

    Returns immediately (202 Accepted) with a task_id. The workflows
    run in the background. Do NOT await completion here.
    """
    if not req.steps:
        raise HTTPException(
            status_code=400,
            detail="steps must not be empty"
        )

    # Validate all workflow names upfront to fail fast
    for step in req.steps:
        if step.workflow_name not in _WORKFLOW_CLASSES:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown workflow: {step.workflow_name}",
            )

    def _make_workflow(step: dict) -> BaseWorkflow:
        """Factory function to instantiate workflows."""
        cls = _WORKFLOW_CLASSES[step["workflow_name"]]
        return cls(
            graph=graph,
            llm_factory=workflow_service.llm_factory,
        )

    try:
        # Prepare steps with cleaned params
        steps = []
        for step in req.steps:
            params = dict(step.params or {})
            params.pop("mode", None)  # legacy cleanup
            steps.append({
                "workflow_name": step.workflow_name,
                "params": params,
            })

        # Submit batch - returns immediately, runs in background
        conv_id, task_id = await workflow_service.run_batch(
            steps=steps,
            workflow_factory=_make_workflow,
            store=store,
            conversation_id=req.conversation_id,
            conversation_title=req.conversation_title,
            conversation_description=req.conversation_description,
        )

        return RunWorkflowBatchResponse(
            conversation_id=conv_id,
            task_id=task_id,
            status="accepted_and_running",
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Batch workflow submission failed")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start workflow batch: {e}",
        ) from e


# Optional: Endpoint to check batch progress or wait (for clients that want to poll)
@router.get("/{task_id}/status")
async def get_task_status(
    task_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Get current status of a workflow task including subtasks.
    """
    status = workflow_service.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": status.id,
        "state": status.state.value,
        "progress": status.progress,
        "progress_message": status.progress_message,
        "sub_task_count": status.sub_task_count,
        "started_at": status.started_at,
        "finished_at": status.finished_at,
        "error": status.error,
    }


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Cancel a running workflow task.
    """
    cancelled = workflow_service.cancel_task(task_id)
    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail="Task not found or already completed"
        )
    return {"task_id": task_id, "status": "cancelled"}
