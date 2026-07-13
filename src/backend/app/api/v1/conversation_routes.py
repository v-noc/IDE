from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, StreamingResponse

from app.agent.schemas.conversation import Conversation, ConversationSummary
from app.agent.schemas.wire import DecisionRequest, SendMessageRequest
from app.agent.service import AgentService
from app.api.dependencies import get_project_uow
from app.db.context import ProjectUoW

router = APIRouter()


def get_agent_service(
    uow: ProjectUoW = Depends(get_project_uow),
) -> AgentService:
    return AgentService(uow)


@router.post(
    "",
    response_model=Conversation,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    service: AgentService = Depends(get_agent_service),
) -> Conversation:
    return await service.create_conversation()


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: AgentService = Depends(get_agent_service),
) -> list[ConversationSummary]:
    return await service.list_conversations(limit=limit, offset=offset)


# Sub-routes before `/{conversation_id:path}` so slashed Terminus ids
# (ConversationSchema/<uuid>) do not swallow /messages, /cancel, etc.
@router.post("/{conversation_id:path}/messages")
async def send_message(
    conversation_id: str,
    body: SendMessageRequest,
    service: AgentService = Depends(get_agent_service),
) -> StreamingResponse:
    # Ensure the conversation exists before opening the stream.
    await service.get_conversation(conversation_id)
    effort = body.options.effort if body.options else None
    try:
        return service.send_message(conversation_id, body.parts, effort=effort)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/{conversation_id:path}/decision",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def decide(
    conversation_id: str,
    body: DecisionRequest,
    service: AgentService = Depends(get_agent_service),
) -> Response:
    await service.decide(
        conversation_id,
        tool_call_id=body.tool_call_id,
        decision=body.decision,
        overrides=body.overrides,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{conversation_id:path}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_run(
    conversation_id: str,
    service: AgentService = Depends(get_agent_service),
) -> Response:
    await service.cancel(conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{conversation_id:path}/artifacts/{doc:path}",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
async def get_artifact(
    conversation_id: str,
    doc: str,
) -> Response:
    return Response(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content="Artifact reload lands when tools ship (Phase 3)",
    )


@router.get("/{conversation_id:path}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    service: AgentService = Depends(get_agent_service),
) -> Conversation:
    return await service.get_conversation(conversation_id)
