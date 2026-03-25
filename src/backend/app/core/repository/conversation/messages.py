"""Message documents: append and paginated read."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.model.conversation_domain import (
    ConversationMessage,
    TaskPart,
)
from app.core.model.conversation_enums import MessageRole
from app.core.model.conversation_nodes import MessageNode
from app.core.model.schemas.conversation_schema import (
    ConversationSchema,
    MessageSchema,
)
from app.db.async_terminus_client import WOQLQuery as WQ

from ._common import (
    new_doc_id,
    parts_from_json,
    parts_to_json,
    terminus_ids_match,
    utcnow,
)

if TYPE_CHECKING:
    from app.db.async_terminus_client import AsyncClient


class MessagesMixin:
    client: "AsyncClient"

    async def _hydrate_task_parts(
        self, messages: list[ConversationMessage]
    ) -> None:
        """Merge Task document fields into ``TaskPart`` rows (ref-in-message pattern)."""
        for mi, msg in enumerate(messages):
            new_parts: list = []
            changed = False
            for p in msg.parts:
                if isinstance(p, TaskPart):
                    doc = await self.get_task(p.task_id)
                    if doc is not None:
                        desc = (
                            (doc.progress_message or "").strip()
                            or (doc.description or "").strip()
                            or p.description
                        )
                        new_parts.append(
                            p.model_copy(
                                update={
                                    "title": doc.name or p.title,
                                    "description": desc,
                                    "state": doc.state,
                                    "progress": doc.progress,
                                    "started_at": doc.started_at or p.started_at,
                                    "finished_at": doc.finished_at or p.finished_at,
                                    "sub_task_count": doc.sub_task_count,
                                    "workflow_name": doc.workflow_name or p.workflow_name,
                                }
                            )
                        )
                        changed = True
                    else:
                        new_parts.append(p)
                else:
                    new_parts.append(p)
            if changed:
                messages[mi] = msg.model_copy(update={"parts": new_parts})

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
        schmea = MessageSchema.from_pydantic(msg_node)
        try:
            await self.client.insert_document(
                schmea,
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
        await self._hydrate_task_parts(out)
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
        msg = ConversationMessage(
            id=node.id,
            role=MessageRole(node.role),
            parts=parts,
            sequence=node.sequence,
            created_at=node.created_at,
            token_count=node.token_count,
            model=node.model_name,
        )
        buf = [msg]
        await self._hydrate_task_parts(buf)
        return buf[0]

    async def update_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
    ) -> bool:
        try:
            raw = await self.client.get_document(message.id)
        except Exception as exc:
            print(exc)
            return False
        if not raw or "MessageSchema" not in str(raw.get("@type", "")):
            return False
        node = MessageNode.from_raw_dict(raw)
        if not terminus_ids_match(node.conversation_id, conversation_id):
            return False
        now = utcnow()
        if isinstance(message.role, MessageRole):
            role_val = message.role.value
        else:
            role_val = str(message.role)
        updated = MessageNode(
            id=message.id,
            conversation_id=conversation_id,
            role=role_val,
            parts_json=parts_to_json(message.parts),
            token_count=message.token_count,
            model_name=message.model,
            sequence=node.sequence,
            created_at=node.created_at,
            updated_at=now,
        )
        try:
            await self.client.update_document(
                MessageSchema.from_pydantic(updated),
                commit_msg=f"Update message {message.id}",
            )
        except Exception as exc:
            print(exc)
            return False
        return True
