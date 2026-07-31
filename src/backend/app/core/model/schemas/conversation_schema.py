import json
from datetime import datetime

import orjson

from app.core.model.conversation import ConversationNode
from .base import BaseSchema


class ConversationSchema(BaseSchema):
    """TerminusDB document for agent conversations.

    Nested message/part unions are stored as ``messages_json`` (string) to
    avoid TerminusDB sys:JSON issues — same pattern as LogSchema.payload.
    """

    project_id: str
    title: str
    status: str
    schema_version: str
    messages_json: str
    artifacts_json: str = "{}"

    @staticmethod
    def from_pydantic(node: ConversationNode) -> "ConversationSchema":
        messages_payload = [m.model_dump(mode="json") for m in node.messages]
        return ConversationSchema(
            _id=node.id,
            name=node.name,
            description=node.title or "",
            project_id=node.project_id,
            title=node.title,
            status=node.status,
            schema_version=node.schema_version,
            messages_json=orjson.dumps(messages_payload).decode(),
            artifacts_json=orjson.dumps(node.artifacts).decode(),
            created_at=node.created_at,
            updated_at=node.updated_at,
        )

    def to_pydantic(self) -> ConversationNode:
        raw_id = self._id
        if isinstance(raw_id, str) and not raw_id.startswith("ConversationSchema/"):
            raw_id = f"ConversationSchema/{raw_id}"

        messages_data = []
        if self.messages_json:
            try:
                messages_data = orjson.loads(self.messages_json)
            except orjson.JSONDecodeError:
                messages_data = json.loads(self.messages_json)

        artifacts_data: dict = {}
        if self.artifacts_json:
            try:
                artifacts_data = orjson.loads(self.artifacts_json)
            except orjson.JSONDecodeError:
                artifacts_data = json.loads(self.artifacts_json)

        return ConversationNode.from_raw_dict(
            {
                "@id": raw_id,
                "name": self.name,
                "project_id": self.project_id,
                "title": self.title,
                "status": self.status,
                "schema_version": self.schema_version,
                "messages": messages_data,
                "artifacts": artifacts_data,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            },
        )
