from __future__ import annotations

from datetime import datetime, timezone

from app.agent.schemas.conversation import (
    Conversation,
    ConversationStatus,
    ConversationSummary,
    Message,
)
from app.core.model.conversation import ConversationNode
from app.core.model.schemas.conversation_schema import ConversationSchema
from app.core.model.schemas import ensure_conversation_schema
from app.core.repository.base_repo import BaseRepo
from app.db.async_terminus_client import AsyncClient


class ConversationRepo(BaseRepo[ConversationNode, ConversationSchema]):
    def __init__(self, client: AsyncClient):
        super().__init__(client, ConversationNode, ConversationSchema)

    async def create_conversation(
        self,
        conversation: Conversation,
    ) -> Conversation | None:
        await ensure_conversation_schema(self.client)
        node = ConversationNode.from_conversation(conversation)
        created = await self.create_nodes(
            node,
            singular_name="conversation",
            plural_name="conversations",
        )
        if created is None:
            return None
        if isinstance(created, list):
            return created[0].to_conversation()
        return created.to_conversation()

    async def get_conversation(
        self,
        conversation_id: str,
    ) -> Conversation | None:
        node = await self.get_by_id(conversation_id)
        if node is None:
            return None
        return node.to_conversation()

    async def list_for_project(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConversationSummary]:
        nodes = await self.get_all(doc_type="ConversationSchema")
        # Newest first
        nodes.sort(key=lambda n: n.updated_at, reverse=True)
        sliced = nodes[offset:offset + limit]
        return [
            ConversationSummary(
                id=n.id,
                title=n.title,
                updated_at=n.updated_at,
                status=n.status,
            )
            for n in sliced
        ]

    async def append_message(
        self,
        conversation_id: str,
        message: Message,
    ) -> Conversation | None:
        conversation = await self.get_conversation(conversation_id)
        if conversation is None:
            return None
        conversation.messages.append(message)
        conversation.updated_at = datetime.now(timezone.utc)
        return await self._save(conversation)

    async def update_message(
        self,
        conversation_id: str,
        message: Message,
    ) -> Conversation | None:
        conversation = await self.get_conversation(conversation_id)
        if conversation is None:
            return None
        replaced = False
        for index, existing in enumerate(conversation.messages):
            if existing.id == message.id:
                conversation.messages[index] = message
                replaced = True
                break
        if not replaced:
            conversation.messages.append(message)
        conversation.updated_at = datetime.now(timezone.utc)
        return await self._save(conversation)

    async def set_status(
        self,
        conversation_id: str,
        status: ConversationStatus,
    ) -> Conversation | None:
        conversation = await self.get_conversation(conversation_id)
        if conversation is None:
            return None
        conversation.status = status
        conversation.updated_at = datetime.now(timezone.utc)
        return await self._save(conversation)

    async def save_conversation(
        self,
        conversation: Conversation,
    ) -> Conversation | None:
        conversation.updated_at = datetime.now(timezone.utc)
        return await self._save(conversation)

    async def _save(self, conversation: Conversation) -> Conversation | None:
        node = ConversationNode.from_conversation(conversation)
        updated = await self.update_node(
            node,
            commit_msg=f"Updating conversation {conversation.id}",
        )
        if updated is None:
            return None
        return updated.to_conversation()
