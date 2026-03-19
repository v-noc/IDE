"""Conversation document CRUD and listing."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from app.agent.models.conversation import Conversation, ConversationSummary
from app.core.model.conversation_nodes import ConversationNode
from app.core.model.schemas.conversation_schema import ConversationSchema

from ._common import new_doc_id, utcnow

if TYPE_CHECKING:
    from app.db.async_terminus_client import AsyncClient


class ConversationsMixin:
    client: "AsyncClient"

    async def create_conversation(
        self,
        title: str,
        description: str = "",
        metadata: dict | None = None,
    ) -> str | None:
        now = utcnow()
        conv_id = new_doc_id("ConversationSchema")
        node = ConversationNode(
            id=conv_id,
            name=title,
            description=description,
            metadata_json=json.dumps(metadata or {}),
            message_count=0,
            has_active_task=False,
            created_at=now,
            updated_at=now,
        )
        try:
            await self.client.insert_document(
                ConversationSchema.from_pydantic(node),
                commit_msg=f"Creating conversation {title!r}",
            )
        except Exception as exc:
            print(exc)
            return None
        return conv_id

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        conv = await self._get_conversation_node(conversation_id)
        if conv is None:
            return None
        messages = await self.get_messages(
            conversation_id, cursor=0, limit=10_000
        )
        meta: dict[str, Any] = {}
        try:
            meta = json.loads(conv.metadata_json or "{}")
        except json.JSONDecodeError:
            meta = {}
        return Conversation(
            id=conv.id,
            title=conv.name,
            description=conv.description,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=conv.message_count,
            has_active_task=conv.has_active_task,
            messages=messages,
            metadata=meta,
        )

    async def _get_conversation_node(
        self, conversation_id: str
    ) -> ConversationNode | None:
        try:
            raw = await self.client.get_document(conversation_id)
        except Exception as exc:
            print(exc)
            return None
        if not raw or "ConversationSchema" not in str(raw.get("@type", "")):
            return None
        return ConversationNode.from_raw_dict(raw)

    async def list_conversations(
        self,
        limit: int = 50,
        cursor: str | None = None,
    ) -> list[ConversationSummary]:
        try:
            items_raw = await self.client.get_all_documents(doc_type="ConversationSchema")
        except Exception as exc:
            print(exc)
            return []
        nodes = [ConversationNode.from_raw_dict(r) for r in items_raw]
        nodes.sort(key=lambda n: n.updated_at, reverse=True)
        if cursor:
            idx = next((i for i, n in enumerate(nodes) if n.id == cursor), None)
            if idx is not None:
                nodes = nodes[idx + 1:]
        cap = max(1, limit)
        return [
            ConversationSummary(
                id=n.id,
                title=n.name,
                description=n.description,
                created_at=n.created_at,
                updated_at=n.updated_at,
                message_count=n.message_count,
                has_active_task=n.has_active_task,
            )
            for n in nodes[:cap]
        ]
