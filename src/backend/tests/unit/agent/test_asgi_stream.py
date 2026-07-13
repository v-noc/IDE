"""httpx ASGI create → stream → reload integration test."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import orjson
import pytest
from httpx import ASGITransport, AsyncClient

from app.agent.schemas.conversation import (
    Conversation,
    ConversationSummary,
    Message,
)
from app.agent.service import AgentService, _active_runs, _cancel_flags
from app.api.v1.conversation_routes import get_agent_service, router
from app.core.model.nodes import ProjectNode
from fastapi import FastAPI


class InMemoryConversationRepo:
    def __init__(self) -> None:
        self._store: dict[str, Conversation] = {}

    async def create_conversation(
        self,
        conversation: Conversation,
    ) -> Conversation:
        saved = conversation.model_copy(deep=True)
        self._store[saved.id] = saved
        return saved.model_copy(deep=True)

    async def get_conversation(
        self,
        conversation_id: str,
    ) -> Conversation | None:
        conv = self._store.get(conversation_id)
        return conv.model_copy(deep=True) if conv else None

    async def list_for_project(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConversationSummary]:
        items = sorted(
            self._store.values(),
            key=lambda c: c.updated_at,
            reverse=True,
        )
        sliced = items[offset:offset + limit]
        return [
            ConversationSummary(
                id=c.id,
                title=c.title,
                updated_at=c.updated_at,
                status=c.status,
            )
            for c in sliced
        ]

    async def append_message(
        self,
        conversation_id: str,
        message: Message,
    ) -> Conversation | None:
        conv = self._store.get(conversation_id)
        if conv is None:
            return None
        conv.messages.append(message.model_copy(deep=True))
        conv.updated_at = datetime.now(timezone.utc)
        return conv.model_copy(deep=True)

    async def update_message(
        self,
        conversation_id: str,
        message: Message,
    ) -> Conversation | None:
        conv = self._store.get(conversation_id)
        if conv is None:
            return None
        for index, existing in enumerate(conv.messages):
            if existing.id == message.id:
                conv.messages[index] = message.model_copy(deep=True)
                break
        else:
            conv.messages.append(message.model_copy(deep=True))
        conv.updated_at = datetime.now(timezone.utc)
        return conv.model_copy(deep=True)

    async def set_status(
        self,
        conversation_id: str,
        status: str,
    ) -> Conversation | None:
        conv = self._store.get(conversation_id)
        if conv is None:
            return None
        conv.status = status  # type: ignore[assignment]
        conv.updated_at = datetime.now(timezone.utc)
        return conv.model_copy(deep=True)

    async def save_conversation(
        self,
        conversation: Conversation,
    ) -> Conversation | None:
        if conversation.id not in self._store:
            return None
        saved = conversation.model_copy(deep=True)
        saved.updated_at = datetime.now(timezone.utc)
        self._store[conversation.id] = saved
        return saved.model_copy(deep=True)


class FakeUoW:
    def __init__(self, project: ProjectNode, repo: InMemoryConversationRepo):
        self.project = project
        self._repo = repo

    def get_project_repos(self):
        return SimpleNamespace(conversation_repo=self._repo)


@pytest.fixture
def asgi_app():
    _active_runs.clear()
    _cancel_flags.clear()

    repo = InMemoryConversationRepo()
    project = ProjectNode(
        id="ProjectSchema/test-project",
        name="test",
        description="test",
        local_path="/tmp/test",
        db_name="test_db",
    )
    service = AgentService(FakeUoW(project, repo))  # type: ignore[arg-type]

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/conversations")
    app.dependency_overrides[get_agent_service] = lambda: service

    yield app, repo

    app.dependency_overrides.clear()
    _active_runs.clear()
    _cancel_flags.clear()


@pytest.mark.asyncio
async def test_asgi_create_stream_reload(asgi_app):
    app, _repo = asgi_app
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        create = await client.post("/api/v1/conversations")
        assert create.status_code == 201
        conversation = create.json()
        conv_id = conversation["id"]
        assert conversation["status"] == "idle"
        assert conversation["messages"] == []

        frames: list[dict] = []
        async with client.stream(
            "POST",
            f"/api/v1/conversations/{conv_id}/messages",
            json={"parts": [{"type": "text", "text": "hello"}]},
        ) as response:
            assert response.status_code == 200
            assert "ndjson" in response.headers["content-type"]
            async for line in response.aiter_lines():
                if line.strip():
                    frames.append(orjson.loads(line))

        assert frames[0]["kind"] == "open"
        assert frames[0]["doc"] == conv_id
        assert any(f["kind"] == "patch" for f in frames)
        assert any(
            op.get("op") == "append"
            for f in frames
            if f.get("kind") == "patch"
            for op in f.get("ops", [])
        )
        assert frames[-1]["kind"] == "close"
        assert frames[-1]["status"] == "idle"

        reload_resp = await client.get(f"/api/v1/conversations/{conv_id}")
        assert reload_resp.status_code == 200
        reloaded = reload_resp.json()
        assert reloaded["status"] == "idle"
        assert len(reloaded["messages"]) == 2
        assert reloaded["messages"][0]["role"] == "user"
        assert reloaded["messages"][1]["role"] == "assistant"
        assert reloaded["messages"][1]["parts"][0]["text"] == "Echo: hello"
        assert reloaded["messages"][1]["metadata"]["model_id"] == "fake:echo"
        assert reloaded["messages"][1]["metadata"]["stop_reason"] == "end_turn"
