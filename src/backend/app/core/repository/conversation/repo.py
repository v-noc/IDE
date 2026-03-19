"""Composed repository for conversations, messages, tasks, and subtasks."""

from __future__ import annotations

from app.db.async_terminus_client import AsyncClient

from .conversations import ConversationsMixin
from .messages import MessagesMixin
from .subtasks import SubtasksMixin
from .tasks import TasksMixin


class ConversationRepo(
    ConversationsMixin,
    MessagesMixin,
    TasksMixin,
    SubtasksMixin,
):
    """TerminusDB: conversations, messages, tasks, and subtasks."""

    def __init__(self, client: AsyncClient):
        self.client = client
