from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from loguru import logger

from app.agent.harness.echo_runner import run_echo
from app.agent.harness.patcher import ConversationPatcher
from app.agent.schemas.constants import HARNESS_SCHEMA_VERSION
from app.agent.schemas.conversation import (
    Conversation,
    ConversationSummary,
    EffortLevel,
    Message,
    MessageMetadata,
)
from app.agent.schemas.parts import Part, TextPart
from app.db.context import ProjectUoW
from app.walkthrough.transport import ndjson_response

# conversation_id → run id (guard concurrent runs)
_active_runs: dict[str, str] = {}
_cancel_flags: dict[str, asyncio.Event] = {}


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

        run_id = f"run-{uuid.uuid4().hex[:8]}"
        _active_runs[conversation_id] = run_id
        _cancel_flags[conversation_id] = asyncio.Event()

        return ndjson_response(
            lambda: self._stream_message(conversation_id, parts, effort=effort),
        )

    async def cancel(self, conversation_id: str) -> None:
        flag = _cancel_flags.get(conversation_id)
        if flag is not None:
            flag.set()
        # Even if no run is active, acknowledge — Phase 4 hardens this.
        return None

    async def _stream_message(
        self,
        conversation_id: str,
        parts: list[Part],
        *,
        effort: EffortLevel | None,
    ):
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        cancel_flag = _cancel_flags.get(conversation_id) or asyncio.Event()

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
                saved = await self._repo().append_message(conversation_id, user_message)
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
                # Persist the assistant skeleton early so a crash leaves a truthful record.
                await self._repo().save_conversation(patcher.conversation)

                user_text = _first_text(parts)
                metadata = await run_echo(
                    patcher,
                    assistant_index=assistant_index,
                    user_text=user_text,
                    cancelled=cancel_flag,
                )
                if effort is not None:
                    metadata.effort = effort

                await patcher.finalize_message(assistant_index, metadata)
                final_status = "idle" if metadata.stop_reason != "error" else "error"
                if metadata.stop_reason == "cancelled":
                    final_status = "idle"
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
                _cancel_flags.pop(conversation_id, None)
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


def _first_text(parts: list[Part]) -> str:
    for part in parts:
        if isinstance(part, TextPart):
            return part.text
    return ""
