
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.api.v1.agent.deps import get_agent_executor
from app.agent.runner.executor import AgentExecutor
from app.agent.workflows.documentation_gen import DocumentationGeneratorWorkflow
# Import other workflows...

router = APIRouter(prefix="/workflows", tags=["Agent Workflows"])


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
):
    """
    Trigger a background workflow (e.g., documentation generation).
    If conversation_id is None, a new conversation is automatically created.
    """

    # 1. Resolve workflow name to class instance
    workflow_map = {
        "documentation_generator": DocumentationGeneratorWorkflow(),
        # "description_generator": DescriptionGeneratorWorkflow(),
    }

    workflow = workflow_map.get(req.workflow_name)
    if not workflow:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown workflow: {req.workflow_name}"
        )

    try:
        # 2. Instruct executor to start the workflow
        # The executor handles creating the TaskPart message and submitting to TaskManager
        conv_id, task_id = await executor.run_workflow(
            workflow=workflow,
            conversation_id=req.conversation_id,
            **req.params
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
