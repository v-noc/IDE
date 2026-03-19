from typing import Any, Optional, Type

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agent.context.graph_traversal import GraphTraversal
from app.agent.runner.executor import AgentExecutor
from app.agent.workflows.base import BaseWorkflow
from app.agent.workflows.description_gen import DescriptionGeneratorWorkflow
from app.agent.workflows.documentation_gen import DocumentationGeneratorWorkflow
from app.api.dependencies import get_project_conversation_store
from app.api.v1.agent.deps import get_agent_executor, get_graph_traversal
from app.agent.conversation_store import ConversationStore


router = APIRouter(prefix="/workflows", tags=["Agent Workflows"])

_WORKFLOW_CLASSES: dict[str, Type[BaseWorkflow]] = {
    "documentation_generator": DocumentationGeneratorWorkflow,
    "description_generator": DescriptionGeneratorWorkflow,
}


# ─── Schemas ──────────────────────────────────────────────

class RunWorkflowRequest(BaseModel):
    workflow_name: str
    params: dict[str, Any]
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None


class RunWorkflowResponse(BaseModel):
    conversation_id: str
    task_id: str
    status: str


# ─── Routes ───────────────────────────────────────────────

@router.post("/run", response_model=RunWorkflowResponse, status_code=202)
async def run_workflow(
    req: RunWorkflowRequest,
    executor: AgentExecutor = Depends(get_agent_executor),
    graph: GraphTraversal = Depends(get_graph_traversal),
):
    """
    Trigger a background workflow (e.g., documentation generation).
    If conversation_id is None, a new conversation is automatically created.
    """

    workflow_cls = _WORKFLOW_CLASSES.get(req.workflow_name)
    if not workflow_cls:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown workflow: {req.workflow_name}"
        )

    workflow = workflow_cls(
        graph=graph,
        llm_factory=executor.llm_factory,
    )

    try:
        params = dict(req.params or {})
        # Keep generations separate by route; ignore legacy combined mode params.
        params.pop("mode", None)

        # 2. Instruct executor to start the workflow
        # The executor handles creating the TaskPart message and submitting to TaskManager
        conv_id, task_id = await executor.run_workflow(
            workflow=workflow,
            conversation_id=req.conversation_id,
            store=store,
            **params,
        )

        # 3. Return accepted status immediately (task is running in background)
        return RunWorkflowResponse(
            conversation_id=conv_id,
            task_id=task_id,
            status="accepted_and_running"
        )

    except ValueError as e:
        # E.g., invalid params or conversation_id doesn't exist
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start workflow: {e}")
