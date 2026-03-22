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
    """Run several workflows in order against one conversation."""

    steps: list[WorkflowBatchStep]
    conversation_id: Optional[str] = None
    conversation_title: Optional[str] = None
    conversation_description: Optional[str] = None


class RunWorkflowBatchResponse(BaseModel):
    conversation_id: str
    task_ids: list[str]
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
        raise HTTPException(
            status_code=500, detail=f"Failed to start workflow: {e}"
        ) from e


@router.post("/run-batch", response_model=RunWorkflowBatchResponse, status_code=202)
async def run_workflow_batch(
    req: RunWorkflowBatchRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
    graph: GraphTraversal = Depends(get_graph_traversal),
    store: ConversationStore = Depends(get_project_conversation_store),
):
    if not req.steps:
        raise HTTPException(status_code=400, detail="steps must not be empty")

    conv_id = req.conversation_id
    task_ids: list[str] = []

    try:
        for index, step in enumerate(req.steps):
            workflow_cls = _WORKFLOW_CLASSES.get(step.workflow_name)
            if not workflow_cls:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown workflow: {step.workflow_name}",
                )

            workflow = workflow_cls(
                graph=graph,
                llm_factory=workflow_service.llm_factory,
            )

            params = dict(step.params or {})
            params.pop("mode", None)
            if index == 0:
                if req.conversation_title is not None:
                    params["conversation_title"] = req.conversation_title
                if req.conversation_description is not None:
                    params["conversation_description"] = (
                        req.conversation_description
                    )

            conv_id, task_id = await workflow_service.run(
                workflow,
                store=store,
                conversation_id=conv_id,
                **params,
            )
            task_ids.append(task_id)
            await workflow_service.join_task(task_id)

        return RunWorkflowBatchResponse(
            conversation_id=conv_id or "",
            task_ids=task_ids,
            status="accepted_and_running",
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start workflow batch: {e}"
        ) from e
