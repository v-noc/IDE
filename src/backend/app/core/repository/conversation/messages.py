"""Message documents: append and paginated read."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.agent.models.conversation import (
    ConversationMessage,
    MessageRole,
)
from app.core.model.conversation_nodes import MessageNode
from app.core.model.schemas.conversation_schema import (
    ConversationSchema,
    MessageSchema,
)
from app.db.async_terminus_client import WOQLQuery as WQ

from ._common import new_doc_id, parts_from_json, parts_to_json, utcnow

if TYPE_CHECKING:
    from app.db.async_terminus_client import AsyncClient


class MessagesMixin:
    client: "AsyncClient"

    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
    ) -> str | None:
        conv = await self._get_conversation_node(conversation_id)
        if conv is None:
            return None
        now = utcnow()
        seq = conv.message_count
        msg_id = message.id or new_doc_id("MessageSchema")
        if isinstance(message.role, MessageRole):
            role_val = message.role.value
        else:
            role_val = str(message.role)
        msg_node = MessageNode(
            id=msg_id,
            conversation_id=conversation_id,
            role=role_val,
            parts_json=parts_to_json(message.parts),
            token_count=message.token_count,
            model_name=message.model,
            sequence=seq,
            created_at=message.created_at or now,
            updated_at=now,
        )
        try:
            await self.client.insert_document(
                MessageSchema.from_pydantic(msg_node),
                commit_msg=f"Message in {conversation_id}",
            )
        except Exception as exc:
            print(exc)
            return None

        conv.message_count = seq + 1
        conv.updated_at = now
        try:
            await self.client.update_document(
                ConversationSchema.from_pydantic(conv),
                commit_msg=f"Bump message_count {conversation_id}",
            )
        except Exception as exc:
            print(exc)
            return None
        return msg_id

    async def get_messages(
        self,
        conversation_id: str,
        cursor: int = 0,
        limit: int = 50,
    ) -> list[ConversationMessage]:
        cursor = max(0, int(cursor))
        cap = max(1, int(limit))
        try:
            filtered = WQ().woql_and(
                WQ().triple("v:msg", "conversation", conversation_id),
                WQ().triple("v:msg", "rdf:type", "@schema:MessageSchema"),
                WQ().triple("v:msg", "sequence", "v:seq"),
                WQ().greater("v:seq", WQ().literal(cursor - 1, "xsd:integer")),
            )
            ordered = WQ().order_by("v:seq", order="asc").limit(cap, filtered)
            query = WQ().select("v:msg_doc").woql_and(
                ordered,
                WQ().read_document("v:msg", "v:msg_doc"),
            )
            result = await self.client.query(query)
        except Exception as exc:
            print(exc)
            return []

        out: list[ConversationMessage] = []
        for row in result.get("bindings", []):
            raw = row.get("msg_doc")
            if not raw:
                continue
            node = MessageNode.from_raw_dict(raw)
            parts = parts_from_json(node.parts_json)
            out.append(
                ConversationMessage(
                    id=node.id,
                    role=MessageRole(node.role),
                    parts=parts,
                    sequence=node.sequence,
                    created_at=node.created_at,
                    token_count=node.token_count,
                    model=node.model_name,
                )
            )
        return out

    async def get_message(self, message_id: str) -> ConversationMessage | None:
        try:
            raw = await self.client.get_document(message_id)
        except Exception as exc:
            print(exc)
            return None
        if not raw or "MessageSchema" not in (raw.get("@type") or ""):
            return None
        node = MessageNode.from_raw_dict(raw)
        parts = parts_from_json(node.parts_json)
        return ConversationMessage(
            id=node.id,
            role=MessageRole(node.role),
            parts=parts,
            sequence=node.sequence,
            created_at=node.created_at,
            token_count=node.token_count,
            model=node.model_name,
        )
