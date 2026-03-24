from __future__ import annotations

from typing import Protocol

from app.core.model.conversation_domain import (
    Conversation,
    ConversationMessage,
    ConversationSummary,
    TaskPart,
)
from app.core.repository.conversation import (
    ConversationRepo,
    terminus_ids_match,
)


class ConversationStore(Protocol):
    async def create_conversation(
        self,
        title: str,
        description: str = "",
        metadata: dict | None = None,
    ) -> str:
        ...

    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
    ) -> str | None:
        ...

    async def get_conversation(
        self, conversation_id: str
    ) -> Conversation | None:
        ...

    async def get_conversation_metadata(
        self, conversation_id: str
    ) -> ConversationSummary | None:
        ...

    async def list_conversations(
        self, limit: int = 50, cursor: str | None = None
    ) -> list[ConversationSummary]:
        ...

    async def list_messages(
        self,
        conversation_id: str,
        cursor: int = 0,
        limit: int = 50,
    ) -> list[ConversationMessage]:
        ...

    async def upsert_task_part(
        self,
        conversation_id: str,
        task_part: TaskPart,
    ) -> None:
        ...


class TerminusConversationStore:
    """Conversation persistence backed by TerminusDB via `ConversationRepo`."""

    def __init__(self, repo: ConversationRepo):
        self._repo = repo

    async def create_conversation(
        self,
        title: str,
        description: str = "",
        metadata: dict | None = None,
    ) -> str:
        cid = await self._repo.create_conversation(
            title, description, metadata
        )
        if cid is None:
            raise RuntimeError(
                "Failed to create conversation in TerminusDB"
            )
        return cid

    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
    ) -> str | None:
        mid = await self._repo.add_message(conversation_id, message)
        if mid is None:
            raise ValueError(
                f"Failed to add message to conversation {conversation_id!r}"
            )
        return mid

    async def get_conversation(
        self, conversation_id: str
    ) -> Conversation | None:
        return await self._repo.get_conversation(conversation_id)

    async def get_conversation_metadata(
        self, conversation_id: str
    ) -> ConversationSummary | None:
        return await self._repo.get_conversation_summary(conversation_id)

    async def list_conversations(
        self, limit: int = 50, cursor: str | None = None
    ) -> list[ConversationSummary]:
        return await self._repo.list_conversations(limit=limit, cursor=cursor)

    async def list_messages(
        self,
        conversation_id: str,
        cursor: int = 0,
        limit: int = 50,
    ) -> list[ConversationMessage]:
        return await self._repo.get_messages(
            conversation_id, cursor=cursor, limit=limit
        )

    async def upsert_task_part(
        self,
        conversation_id: str,
        task_part: TaskPart,
    ) -> None:
        conv = await self._repo.get_conversation(conversation_id)
        if conv is None:
            raise ValueError(f"Conversation not found: {conversation_id}")

        for message in reversed(conv.messages):
            for idx, part in enumerate(message.parts):
                if isinstance(part, TaskPart) and terminus_ids_match(
                    part.task_id, task_part.task_id
                ):
                    new_parts = list(message.parts)
                    new_parts[idx] = task_part
                    updated = message.model_copy(update={"parts": new_parts})
                    ok = await self._repo.update_message(
                        conversation_id, updated
                    )
                    if not ok:
                        raise ValueError(
                            f"Failed to update message {message.id} "
                            f"for task part"
                        )
                    return

        raise ValueError(
            f"TaskPart not found for task_id={task_part.task_id} "
            f"in conversation={conversation_id}"
        )
