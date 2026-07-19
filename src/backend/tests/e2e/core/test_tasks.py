from urllib.parse import quote

import pytest
from httpx import AsyncClient


def _qs(project_id: str, **params: str) -> str:
    parts = [f"project_id={quote(project_id, safe='')}"]
    for key, value in params.items():
        parts.append(f"{key}={quote(value, safe='')}")
    return "?" + "&".join(parts)


@pytest.mark.asyncio
async def test_task_mutations_with_slash_ids(client: AsyncClient, sample_project_node):
    project_id = sample_project_node.id

    create_resp = await client.post(
        f"/api/v1/tasks/{_qs(project_id)}",
        json={"title": "Fix logging bug", "task_type": "bug", "priority": "high"},
    )
    assert create_resp.status_code == 201
    task = create_resp.json()
    task_id = task["id"]
    assert "/" in task_id

    move_resp = await client.post(
        f"/api/v1/tasks/move{_qs(project_id, task_id=task_id)}",
        json={"status": "in_progress", "rank": "U"},
    )
    assert move_resp.status_code == 200
    assert move_resp.json()["status"] == "in_progress"

    patch_resp = await client.patch(
        f"/api/v1/tasks/{_qs(project_id, task_id=task_id)}",
        json={"title": "Fix logging bug (updated)"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "Fix logging bug (updated)"

    note_resp = await client.post(
        f"/api/v1/tasks/notes{_qs(project_id, task_id=task_id)}",
        json={"text": "Moved to In progress"},
    )
    assert note_resp.status_code == 200

    subtask_resp = await client.post(
        f"/api/v1/tasks/subtasks{_qs(project_id, task_id=task_id)}",
        json={"title": "Write regression test"},
    )
    assert subtask_resp.status_code == 200
    assert subtask_resp.json()["title"] == "Write regression test"

    board_resp = await client.get(f"/api/v1/tasks/board{_qs(project_id)}")
    assert board_resp.status_code == 200
    cache_control = board_resp.headers.get("cache-control", "")
    assert "max-age" not in cache_control.lower()
