from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from loguru import logger

from app.agent.harness.degraded import count_degraded_tools
from app.agent.harness.loop import resume_agent_turn
from app.agent.harness.patcher import ConversationPatcher
from app.agent.harness.runner import run_turn
from app.agent.harness.title import maybe_title
from app.agent.schemas.constants import HARNESS_SCHEMA_VERSION
from app.agent.schemas.conversation import (
    Conversation,
    ConversationSummary,
    EffortLevel,
    Message,
    MessageMetadata,
)
from app.agent.schemas.parts import DecisionPart, Part, TextPart
from app.db.context import ProjectUoW
from app.walkthrough.transport import ndjson_response


@dataclass
class _ActiveRun:
    run_id: str
    cancel: asyncio.Event = field(default_factory=asyncio.Event)
    resume_queue: asyncio.Queue = field(default_factory=asyncio.Queue)


_active_runs: dict[str, _ActiveRun] = {}


class AgentService:
    def __init__(self, uow: ProjectUoW):
        self.uow = uow

    def _repo(self):
        return self.uow.get_project_repos().conversation_repo

    def _project_id(self) -> str:
        project = self.uow.project
        if project is None or not project.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project context is required",
            )
        return project.id

    async def create_conversation(self) -> Conversation:
        now = datetime.now(timezone.utc)
        conversation = Conversation(
            id=f"ConversationSchema/{uuid.uuid4()}",
            project_id=self._project_id(),
            title="",
            created_at=now,
            updated_at=now,
            status="idle",
            messages=[],
            schema_version=HARNESS_SCHEMA_VERSION,
        )
        created = await self._repo().create_conversation(conversation)
        if created is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create conversation",
            )
        return created

    async def list_conversations(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConversationSummary]:
        return await self._repo().list_for_project(limit=limit, offset=offset)

    async def get_conversation(self, conversation_id: str) -> Conversation:
        conversation = await self._repo().get_conversation(conversation_id)
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation not found: {conversation_id}",
            )
        return conversation

    def send_message(
        self,
        conversation_id: str,
        parts: list[Part],
        *,
        effort: EffortLevel | None = None,
    ):
        if conversation_id in _active_runs:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "A run is already active for this conversation.",
                    "conversation_id": conversation_id,
                },
            )

        run = _ActiveRun(run_id=f"run-{uuid.uuid4().hex[:8]}")
        _active_runs[conversation_id] = run

        return ndjson_response(
            lambda: self._stream_message(conversation_id, parts, effort=effort),
        )

    async def decide(
        self,
        conversation_id: str,
        *,
        tool_call_id: str,
        decision: str,
        overrides: dict[str, Any] | None = None,
    ) -> None:
        run = _active_runs.get(conversation_id)
        conversation = await self.get_conversation(conversation_id)
        if run is None:
            if conversation.status != "awaiting_confirmation":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="No active run awaiting confirmation",
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Confirmation stream is no longer open — resync via GET",
            )
        await run.resume_queue.put(
            {
                "tool_call_id": tool_call_id,
                "decision": decision,
                "overrides": overrides or {},
            },
        )

    async def cancel(self, conversation_id: str) -> None:
        """Abort the active run (composer stop). Distinct from confirm-card cancel."""
        run = _active_runs.get(conversation_id)
        if run is not None:
            run.cancel.set()

    async def _stream_message(
        self,
        conversation_id: str,
        parts: list[Part],
        *,
        effort: EffortLevel | None,
    ):
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        run = _active_runs[conversation_id]
        cancel_flag = run.cancel

        async def emit(frame: dict[str, Any]) -> None:
            await queue.put(frame)

        async def producer() -> None:
            try:
                conversation = await self.get_conversation(conversation_id)

                user_message = Message(
                    id=f"msg-{uuid.uuid4().hex[:12]}",
                    role="user",
                    parts=parts,
                )
                saved = await self._repo().append_message(
                    conversation_id, user_message,
                )
                if saved is None:
                    await queue.put(
                        {
                            "kind": "close",
                            "doc": conversation_id,
                            "status": "error",
                            "message": "Failed to persist user message",
                        },
                    )
                    return
                conversation = saved

                async def on_persist(conv: Conversation) -> None:
                    await self._repo().save_conversation(conv)

                patcher = ConversationPatcher(
                    conversation,
                    emit,
                    on_persist=on_persist,
                )
                await patcher.open_conversation()
                await patcher.set_status("running")

                assistant = Message(
                    id=f"msg-{uuid.uuid4().hex[:12]}",
                    role="assistant",
                    parts=[],
                    metadata=MessageMetadata(effort=effort),
                )
                assistant_index = await patcher.add_message(assistant)
                await self._repo().save_conversation(patcher.conversation)

                metadata = await run_turn(
                    patcher,
                    conversation=patcher.conversation,
                    assistant_index=assistant_index,
                    uow=self.uow,
                    effort=effort,
                    cancelled=cancel_flag,
                    emit=emit,
                )

                # Pause stream while awaiting confirmation; resume on /decision
                while patcher.conversation.status == "awaiting_confirmation":
                    if cancel_flag.is_set():
                        metadata = MessageMetadata(
                            model_id=metadata.model_id,
                            prompt_version=metadata.prompt_version,
                            effort=effort,
                            stop_reason="cancelled",
                            duration_ms=metadata.duration_ms,
                            usage=metadata.usage,
                            cost_usd=metadata.cost_usd,
                        )
                        break

                    get_decision = asyncio.create_task(run.resume_queue.get())
                    wait_cancel = asyncio.create_task(cancel_flag.wait())
                    done, pending = await asyncio.wait(
                        {get_decision, wait_cancel},
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    for task in pending:
                        task.cancel()
                    if wait_cancel in done and cancel_flag.is_set():
                        metadata = MessageMetadata(
                            model_id=metadata.model_id,
                            prompt_version=metadata.prompt_version,
                            effort=effort,
                            stop_reason="cancelled",
                            duration_ms=metadata.duration_ms,
                            usage=metadata.usage,
                            cost_usd=metadata.cost_usd,
                        )
                        break
                    decision = None
                    if get_decision in done and not get_decision.cancelled():
                        try:
                            decision = get_decision.result()
                        except Exception:
                            decision = None
                    if decision is None:
                        continue

                    dpart = DecisionPart(
                        tool_call_id=decision.get("tool_call_id") or "",
                        decision=decision.get("decision") or "cancel",
                        overrides=decision.get("overrides") or {},
                    )
                    await patcher.add_part(assistant_index, dpart)

                    # Confirm-card cancel resumes with "declined by user";
                    # only POST /cancel aborts the whole run.
                    metadata = await resume_agent_turn(
                        patcher,
                        conversation=patcher.conversation,
                        assistant_index=assistant_index,
                        uow=self.uow,
                        decision=decision,
                        effort=effort,
                        cancelled=cancel_flag,
                        emit=emit,
                    )

                if cancel_flag.is_set() and metadata.stop_reason != "error":
                    metadata.stop_reason = "cancelled"

                if effort is not None and metadata.effort is None:
                    metadata.effort = effort

                # Degraded honesty: one short note when a tool fell back
                degraded = count_degraded_tools(
                    patcher.conversation, assistant_index,
                )
                if degraded and metadata.stop_reason == "end_turn":
                    note = (
                        f"\n\n({degraded} tool step"
                        f"{'s' if degraded != 1 else ''} ran degraded.)"
                    )
                    # Append to last text part or add one
                    parts_list = patcher.conversation.messages[
                        assistant_index
                    ].parts
                    text_idx = next(
                        (
                            i for i, p in enumerate(parts_list)
                            if isinstance(p, TextPart)
                        ),
                        None,
                    )
                    if text_idx is not None:
                        await patcher.append_text(
                            assistant_index, text_idx, note,
                        )
                    else:
                        await patcher.add_part(
                            assistant_index, TextPart(text=note.strip()),
                        )

                await patcher.finalize_message(assistant_index, metadata)

                # Title after first completed turn
                title = maybe_title(patcher.conversation)
                if title:
                    await patcher.set_title(title)

                final_status = "idle"
                if metadata.stop_reason == "error":
                    final_status = "error"
                await patcher.set_status(final_status)
                await self._repo().save_conversation(patcher.conversation)
                await patcher.close_doc(conversation_id, final_status)
            except Exception as exc:
                logger.exception("Agent run failed for {}", conversation_id)
                try:
                    await self._repo().set_status(conversation_id, "error")
                except Exception:
                    pass
                await queue.put(
                    {
                        "kind": "close",
                        "doc": conversation_id,
                        "status": "error",
                        "message": str(exc),
                    },
                )
            finally:
                _active_runs.pop(conversation_id, None)
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
