from __future__ import annotations

import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Protocol

from app.agent.models.conversation import (
    Conversation,
    ConversationMessage,
    ConversationSummary,
    TaskPart,
)


class ConversationStore(Protocol):
    def create_conversation(
        self,
        title: str,
        description: str = "",
        metadata: dict | None = None,
    ) -> str:
        ...

    def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
    ) -> None:
        ...

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        ...

    def list_conversations(self, limit: int = 50) -> list[ConversationSummary]:
        ...

    def upsert_task_part(
        self,
        conversation_id: str,
        task_part: TaskPart,
    ) -> None:
        ...


class InMemoryConversationStore:
    """Simple process-local conversation store."""

    def __init__(self):
        self._lock = threading.Lock()
        self._conversations: dict[str, Conversation] = {}

    def create_conversation(
        self,
        title: str,
        description: str = "",
        metadata: dict | None = None,
    ) -> str:
        conversation_id = str(uuid.uuid4())
        now = datetime.utcnow()
        conversation = Conversation(
            id=conversation_id,
            title=title,
            description=description,
            created_at=now,
            updated_at=now,
            messages=[],
            metadata=metadata or {},
        )
        with self._lock:
            self._conversations[conversation_id] = conversation
        return conversation_id

    def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
    ) -> None:
        with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation is None:
                raise ValueError(f"Conversation not found: {conversation_id}")
            conversation.messages.append(message)
            conversation.updated_at = datetime.utcnow()
            conversation.message_count = len(conversation.messages)

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation is None:
                return None
            return Conversation.model_validate(conversation.model_dump())

    def list_conversations(self, limit: int = 50) -> list[ConversationSummary]:
        with self._lock:
            conversations = sorted(
                self._conversations.values(),
                key=lambda item: item.updated_at,
                reverse=True,
            )
            sliced = conversations[: max(1, limit)]
            return [
                ConversationSummary(
                    id=item.id,
                    title=item.title,
                    description=item.description,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    message_count=len(item.messages),
                )
                for item in sliced
            ]

    def upsert_task_part(
        self,
        conversation_id: str,
        task_part: TaskPart,
    ) -> None:
        with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation is None:
                raise ValueError(f"Conversation not found: {conversation_id}")

            for message in reversed(conversation.messages):
                replaced = False
                for idx, part in enumerate(message.parts):
                    if (
                        isinstance(part, TaskPart)
                        and part.task_id == task_part.task_id
                    ):
                        message.parts[idx] = task_part
                        replaced = True
                        break
                if replaced:
                    conversation.updated_at = datetime.utcnow()
                    return

            raise ValueError(
                f"TaskPart not found for task_id={task_part.task_id} "
                f"in conversation={conversation_id}"
            )


class SQLiteConversationStore:
    """SQLite-backed conversation store with the same interface."""

    def __init__(
        self,
        db_path: str,
    ):
        self.db_path = db_path
        self._lock = threading.Lock()
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    message_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                ON conversation_messages(conversation_id, created_at)
                """
            )
            conn.commit()

    def create_conversation(
        self,
        title: str,
        description: str = "",
        metadata: dict | None = None,
    ) -> str:
        conversation_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        metadata_json = "{}"
        if metadata:
            from json import dumps

            metadata_json = dumps(metadata)

        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO conversations (
                        id, title, description, metadata_json, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        conversation_id,
                        title,
                        description,
                        metadata_json,
                        now,
                        now,
                    ),
                )
                conn.commit()
        return conversation_id

    def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage,
    ) -> None:
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT id FROM conversations WHERE id = ?",
                    (conversation_id,),
                ).fetchone()
                if row is None:
                    raise ValueError(
                        f"Conversation not found: {conversation_id}"
                    )

                message_json = message.model_dump_json()
                created_at = datetime.utcnow().isoformat()
                conn.execute(
                    """
                    INSERT INTO conversation_messages (
                        id, conversation_id, message_json, created_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (message.id, conversation_id, message_json, created_at),
                )
                conn.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (created_at, conversation_id),
                )
                conn.commit()

    def get_conversation(
        self,
        conversation_id: str,
    ) -> Conversation | None:
        from json import loads

        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    """
                    SELECT
                        id,
                        title,
                        description,
                        metadata_json,
                        created_at,
                        updated_at
                    FROM conversations
                    WHERE id = ?
                    """,
                    (conversation_id,),
                ).fetchone()
                if row is None:
                    return None

                message_rows = conn.execute(
                    """
                    SELECT message_json
                    FROM conversation_messages
                    WHERE conversation_id = ?
                    ORDER BY created_at ASC
                    """,
                    (conversation_id,),
                ).fetchall()

        messages = [
            ConversationMessage.model_validate_json(item["message_json"])
            for item in message_rows
        ]
        metadata = loads(row["metadata_json"]) if row["metadata_json"] else {}
        created_at = datetime.fromisoformat(row["created_at"])
        updated_at = datetime.fromisoformat(row["updated_at"])

        return Conversation(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            created_at=created_at,
            updated_at=updated_at,
            message_count=len(messages),
            messages=messages,
            metadata=metadata,
        )

    def list_conversations(self, limit: int = 50) -> list[ConversationSummary]:
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT
                        c.id,
                        c.title,
                        c.description,
                        c.created_at,
                        c.updated_at,
                        (
                            SELECT COUNT(1)
                            FROM conversation_messages m
                            WHERE m.conversation_id = c.id
                        ) AS message_count
                    FROM conversations c
                    ORDER BY c.updated_at DESC
                    LIMIT ?
                    """,
                    (max(1, limit),),
                ).fetchall()

        return [
            ConversationSummary(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                message_count=row["message_count"],
            )
            for row in rows
        ]

    def upsert_task_part(
        self,
        conversation_id: str,
        task_part: TaskPart,
    ) -> None:
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT id, message_json
                    FROM conversation_messages
                    WHERE conversation_id = ?
                    ORDER BY created_at DESC
                    """,
                    (conversation_id,),
                ).fetchall()

                for row in rows:
                    msg = ConversationMessage.model_validate_json(
                        row["message_json"]
                    )
                    replaced = False
                    for idx, part in enumerate(msg.parts):
                        if (
                            isinstance(part, TaskPart)
                            and part.task_id == task_part.task_id
                        ):
                            msg.parts[idx] = task_part
                            replaced = True
                            break
                    if not replaced:
                        continue

                    conn.execute(
                        (
                            "UPDATE conversation_messages "
                            "SET message_json = ? WHERE id = ?"
                        ),
                        (msg.model_dump_json(), row["id"]),
                    )
                    conn.execute(
                        "UPDATE conversations SET updated_at = ? WHERE id = ?",
                        (datetime.utcnow().isoformat(), conversation_id),
                    )
                    conn.commit()
                    return

                raise ValueError(
                    (
                        f"TaskPart not found for task_id={task_part.task_id} "
                        f"in conversation={conversation_id}"
                    )
                )
