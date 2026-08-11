import pytest

from app.core.services.task_service import TaskService, TaskServiceError, mid_rank


class TestMidRank:
    def test_initial_rank(self):
        assert mid_rank(None, None) == "U"

    def test_insert_before(self):
        rank = mid_rank(None, "U")
        assert rank < "U"

    def test_insert_between(self):
        rank = mid_rank("A", "C")
        assert "A" < rank < "C"


@pytest.mark.asyncio
async def test_create_and_move_task(project_uow):
    service = TaskService(project_uow)
    created = await service.create_task(
        title="Fix logging bug",
        task_type="bug",
        priority="high",
    )
    assert created["key"] == "VN-1"
    assert created["title"] == "Fix logging bug"
    assert created["status"] == "todo"

    moved = await service.move_task(
        created["id"],
        status="in_progress",
        rank=mid_rank(None, "U"),
    )
    assert moved["status"] == "in_progress"


@pytest.mark.asyncio
async def test_subtask_cycle_refused(project_uow):
    service = TaskService(project_uow)
    parent = await service.create_task(title="Epic parent", task_type="epic")
    child = await service.create_task(title="Child task")
    await service.add_subtask(parent["id"], child_id=child["id"])

    with pytest.raises(TaskServiceError) as exc:
        await service.add_subtask(child["id"], child_id=parent["id"])
    assert "cycle" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_board_bootstrap(project_uow):
    service = TaskService(project_uow)
    payload = await service.get_board_payload()
    assert len(payload["board"]["columns"]) == 5
    assert payload["board"]["columns"][-1]["is_done"] is True


@pytest.mark.asyncio
async def test_shared_subtask_dag(project_uow):
    service = TaskService(project_uow)
    epic_a = await service.create_task(title="Epic A", task_type="epic")
    epic_b = await service.create_task(title="Epic B", task_type="epic")
    shared = await service.create_task(title="Refactor dd()")
    await service.add_subtask(epic_a["id"], child_id=shared["id"])
    await service.add_subtask(epic_b["id"], child_id=shared["id"])

    payload = await service.get_board_payload()
    shared_task = next(t for t in payload["tasks"] if t["id"] == shared["id"])
    parent_a = next(t for t in payload["tasks"] if t["id"] == epic_a["id"])
    assert any(s["id"] == shared["id"] for s in parent_a["subtasks"])
    assert shared_task["subtask_progress"]["total"] == 0
