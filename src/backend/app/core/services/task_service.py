from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.core.model.schemas.task_schema import default_board_node
from app.core.model.tasks import BoardColumn, BoardNode, TaskAnchor, TaskNode, TaskNote
from app.core.socket.manager import get_socket_manager
from app.db.context import ProjectUoW

logger = logging.getLogger(__name__)

BOARD_ID = "BoardSchema/default"
RANK_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
RANK_MIN = RANK_ALPHABET[0]
RANK_MAX = RANK_ALPHABET[-1]
RANK_MID = RANK_ALPHABET[len(RANK_ALPHABET) // 2]


class TaskServiceError(Exception):
    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.status_code = status_code


class TaskService:
    def __init__(self, uow: ProjectUoW):
        self.uow = uow
        self.socket_manager = get_socket_manager()

    @property
    def repos(self):
        return self.uow.get_project_repos()

    async def _ensure_schema(self) -> None:
        await self.repos.task_repo.ensure_schema()

    async def _emit_changed(self, *, summary: bool = False) -> None:
        try:
            project_id = self.uow.project.id if self.uow.project else ""
            if not project_id:
                return
            await self.socket_manager.emit_to_project(
                project_id,
                "tasks.changed",
                {"project_id": project_id},
            )
            if summary:
                await self.socket_manager.emit_to_project(
                    project_id,
                    "tasks.summary_changed",
                    {"project_id": project_id},
                )
        except Exception as exc:
            logger.warning("Failed to emit task socket events: %s", exc)

    async def get_board_payload(self) -> dict[str, Any]:
        await self._ensure_schema()
        board = await self._get_or_create_board()
        tasks = await self.repos.task_repo.get_all(doc_type="TaskSchema")
        task_by_id = {t.id: t for t in tasks}
        done_columns = {c.id for c in board.columns if c.is_done}
        anchor_ids = {
            a.node_id for t in tasks for a in t.anchors if a.node_id
        }
        resolved_ids = await self._resolve_anchor_ids(anchor_ids)

        enriched = [
            self._enrich_task(t, task_by_id, done_columns, resolved_ids)
            for t in tasks
        ]
        enriched.sort(key=lambda t: (t["status"], t["rank"]))

        return {
            "board": {
                "id": board.id,
                "columns": [c.model_dump() for c in board.columns],
                "task_counter": board.task_counter,
            },
            "tasks": enriched,
        }

    async def create_task(
        self,
        *,
        title: str,
        task_type: str = "task",
        priority: str = "none",
        description: str = "",
        labels: set[str] | None = None,
        status: str | None = None,
        anchors: list[dict[str, str]] | None = None,
        subtask_of: str | None = None,
    ) -> dict[str, Any]:
        await self._ensure_schema()
        board = await self._get_or_create_board()
        column_id = status or self._default_create_column_id(board)
        self._validate_column(board, column_id)

        task_id = f"TaskSchema/{uuid4()}"
        key = await self._mint_key(board)
        rank = self._rank_at_top(
            await self.repos.task_repo.get_all(doc_type="TaskSchema"),
            column_id,
        )

        resolved_anchors: list[TaskAnchor] = []
        for anchor in anchors or []:
            node_id = anchor.get("node_id", "")
            if node_id:
                resolved_anchors.append(await self._snapshot_anchor(node_id))

        now = datetime.now(timezone.utc)
        task = TaskNode(
            id=task_id,
            key=key,
            name=title,
            description=description,
            task_type=task_type,
            status=column_id,
            priority=priority,
            labels=labels or set(),
            rank=rank,
            anchors=resolved_anchors,
            notes=[
                TaskNote(
                    text=f"Created as {key}",
                    at=now,
                    origin="system",
                ),
            ],
            created_at=now,
            updated_at=now,
        )

        created = await self.repos.task_repo.create_nodes(
            task,
            singular_name="task",
            plural_name="tasks",
        )
        if created is None:
            raise TaskServiceError("Failed to create task", 500)

        if subtask_of:
            parent = await self.repos.task_repo.get_by_id(subtask_of)
            if parent is None:
                raise TaskServiceError(f"Parent task {subtask_of} not found", 404)
            await self._add_subtask_edge(parent, task_id)

        await self._emit_changed(summary=True)
        payload = await self.get_board_payload()
        return next(t for t in payload["tasks"] if t["id"] == task_id)

    async def update_task(
        self,
        task_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        task_type: str | None = None,
        priority: str | None = None,
        labels: set[str] | None = None,
    ) -> dict[str, Any]:
        task = await self._get_task_or_raise(task_id)
        notes = list(task.notes)
        now = datetime.now(timezone.utc)

        if title is not None:
            stripped = title.strip()
            if not stripped:
                raise TaskServiceError("A task needs a title.", 422)
            task.name = stripped
        if description is not None:
            task.description = description
        if task_type is not None and task_type != task.task_type:
            notes.append(
                TaskNote(
                    text=f"Type changed to {task_type}",
                    at=now,
                    origin="system",
                ),
            )
            task.task_type = task_type
        if priority is not None and priority != task.priority:
            notes.append(
                TaskNote(
                    text=f"Priority changed to {priority}",
                    at=now,
                    origin="system",
                ),
            )
            task.priority = priority
        if labels is not None:
            task.labels = labels

        task.notes = notes
        task.updated_at = now
        await self._save_task(task)
        await self._emit_changed()
        return await self._get_enriched_task(task_id)

    async def move_task(
        self,
        task_id: str,
        *,
        status: str,
        rank: str,
    ) -> dict[str, Any]:
        board = await self._get_or_create_board()
        self._validate_column(board, status)
        task = await self._get_task_or_raise(task_id)
        old_status = task.status
        task.status = status
        all_tasks = await self.repos.task_repo.get_all(doc_type="TaskSchema")
        column_tasks = sorted(
            [t for t in all_tasks if t.status == status and t.id != task_id],
            key=lambda t: t.rank,
        )
        task.rank = rank
        if any(t.rank == rank for t in column_tasks):
            for i, col_task in enumerate(column_tasks):
                if col_task.rank == rank:
                    next_rank = (
                        column_tasks[i + 1].rank
                        if i + 1 < len(column_tasks)
                        else None
                    )
                    task.rank = mid_rank(rank, next_rank)
                    break
        task.updated_at = datetime.now(timezone.utc)
        if old_status != status:
            column_title = next(
                (c.title for c in board.columns if c.id == status),
                status,
            )
            task.notes = [
                *task.notes,
                TaskNote(
                    text=f"Moved to {column_title}",
                    at=task.updated_at,
                    origin="system",
                ),
            ]
        await self._save_task(task)
        await self._emit_changed(summary=True)
        return await self._get_enriched_task(task_id)

    async def delete_task(self, task_id: str) -> None:
        all_tasks = await self.repos.task_repo.get_all(doc_type="TaskSchema")
        to_update: list[TaskNode] = []
        for task in all_tasks:
            changed = False
            if task_id in task.subtask_ids:
                task.subtask_ids.discard(task_id)
                changed = True
            if task_id in task.blocked_by_ids:
                task.blocked_by_ids.discard(task_id)
                changed = True
            if changed:
                task.updated_at = datetime.now(timezone.utc)
                to_update.append(task)

        if to_update:
            await self.repos.task_repo.update_nodes(
                to_update,
                commit_msg=f"Unlink deleted task {task_id}",
                update_schema=lambda _e, _n, _s: None,
            )

        deleted = await self.repos.task_repo.delete_with_parent_cleanup(
            task_id,
            parent_field="subtasks",
            commit_msg=f"Delete task {task_id}",
        )
        if not deleted:
            raise TaskServiceError(f"Task {task_id} not found", 404)
        await self._emit_changed(summary=True)

    async def add_subtask(
        self,
        parent_id: str,
        *,
        child_id: str | None = None,
        inline: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        parent = await self._get_task_or_raise(parent_id)
        if child_id is None:
            if not inline:
                raise TaskServiceError("child_id or inline payload required", 422)
            child = await self.create_task(**inline)
            child_id = child["id"]
        else:
            child_task = await self.repos.task_repo.get_by_id(child_id)
            if child_task is None:
                raise TaskServiceError(f"Child task {child_id} not found", 404)

        await self._add_subtask_edge(parent, child_id)
        await self._emit_changed(summary=True)
        return await self._get_enriched_task(child_id)

    async def remove_subtask(self, parent_id: str, child_id: str) -> None:
        parent = await self._get_task_or_raise(parent_id)
        if child_id not in parent.subtask_ids:
            raise TaskServiceError(
                f"{parent.key} is not a parent of {child_id}",
                404,
            )
        parent.subtask_ids.discard(child_id)
        parent.updated_at = datetime.now(timezone.utc)
        await self._save_task(parent)
        await self._emit_changed(summary=True)

    async def add_blocked_by(self, task_id: str, blocker_id: str) -> dict[str, Any]:
        task = await self._get_task_or_raise(task_id)
        blocker = await self._get_task_or_raise(blocker_id)
        await self._validate_no_cycle(task.id, blocker.id, edge="blocked_by")
        task.blocked_by_ids.add(blocker.id)
        task.updated_at = datetime.now(timezone.utc)
        await self._save_task(task)
        await self._emit_changed()
        return await self._get_enriched_task(task_id)

    async def remove_blocked_by(self, task_id: str, blocker_id: str) -> None:
        task = await self._get_task_or_raise(task_id)
        task.blocked_by_ids.discard(blocker_id)
        task.updated_at = datetime.now(timezone.utc)
        await self._save_task(task)
        await self._emit_changed()

    async def add_anchor(self, task_id: str, node_id: str) -> dict[str, Any]:
        task = await self._get_task_or_raise(task_id)
        anchor = await self._snapshot_anchor(node_id)
        if any(a.node_id == anchor.node_id for a in task.anchors):
            return await self._get_enriched_task(task_id)
        task.anchors.append(anchor)
        task.updated_at = datetime.now(timezone.utc)
        task.notes = [
            *task.notes,
            TaskNote(
                text=f"anchored to {anchor.qname}",
                at=task.updated_at,
                origin="system",
            ),
        ]
        await self._save_task(task)
        await self._emit_changed(summary=True)
        return await self._get_enriched_task(task_id)

    async def remove_anchor(self, task_id: str, node_id: str) -> dict[str, Any]:
        task = await self._get_task_or_raise(task_id)
        before = len(task.anchors)
        removed_qnames = [a.qname for a in task.anchors if a.node_id == node_id]
        task.anchors = [a for a in task.anchors if a.node_id != node_id]
        if len(task.anchors) == before:
            return await self._get_enriched_task(task_id)
        qname = removed_qnames[0] if removed_qnames else node_id
        task.updated_at = datetime.now(timezone.utc)
        task.notes = [
            *task.notes,
            TaskNote(
                text=f"unlinked {qname}",
                at=task.updated_at,
                origin="system",
            ),
        ]
        await self._save_task(task)
        await self._emit_changed(summary=True)
        return await self._get_enriched_task(task_id)

    async def move_anchor(
        self,
        task_id: str,
        *,
        from_node_id: str,
        to_node_id: str,
    ) -> dict[str, Any]:
        task = await self._get_task_or_raise(task_id)
        src = next((a for a in task.anchors if a.node_id == from_node_id), None)
        if src is None:
            raise TaskServiceError(
                f"{task.key} has no anchor on {from_node_id}",
                404,
            )
        new_anchor = await self._snapshot_anchor(to_node_id)
        other_anchors = [a for a in task.anchors if a is not src]
        if any(a.node_id == new_anchor.node_id for a in other_anchors):
            task.anchors = [a for a in task.anchors if a is not src]
            note_text = f"anchor {src.qname} merged into {new_anchor.qname}"
        else:
            idx = task.anchors.index(src)
            task.anchors[idx] = new_anchor
            note_text = f"re-anchored {src.qname} → {new_anchor.qname}"
        task.updated_at = datetime.now(timezone.utc)
        task.notes = [
            *task.notes,
            TaskNote(
                text=note_text,
                at=task.updated_at,
                origin="system",
            ),
        ]
        await self._save_task(task)
        await self._emit_changed(summary=True)
        return await self._get_enriched_task(task_id)

    async def add_note(self, task_id: str, text: str) -> dict[str, Any]:
        task = await self._get_task_or_raise(task_id)
        task.notes = [
            *task.notes,
            TaskNote(
                text=text,
                at=datetime.now(timezone.utc),
                origin="user",
            ),
        ]
        task.updated_at = datetime.now(timezone.utc)
        await self._save_task(task)
        await self._emit_changed()
        return await self._get_enriched_task(task_id)

    async def update_board(self, columns: list[dict[str, Any]]) -> dict[str, Any]:
        board = await self._get_or_create_board()
        board = self._normalize_board_columns(board)
        tasks = await self.repos.task_repo.get_all(doc_type="TaskSchema")
        self._validate_board_columns_update(board, columns)
        new_columns = [BoardColumn(**c) for c in columns]
        new_ids = {c.id for c in new_columns}
        old_ids = {c.id for c in board.columns}

        for removed_id in old_ids - new_ids:
            remaining = [t for t in tasks if t.status == removed_id]
            move_to = next(
                (c.get("move_to") for c in columns if c.get("id") == removed_id),
                None,
            )
            if remaining and not move_to:
                col_title = next(
                    (c.title for c in board.columns if c.id == removed_id),
                    removed_id,
                )
                raise TaskServiceError(
                    f"'{col_title}' still has {len(remaining)} tasks — "
                    "choose a column to move them to.",
                )
            if remaining and move_to:
                self._validate_column(board, move_to)
                for task in remaining:
                    task.status = move_to
                    task.updated_at = datetime.now(timezone.utc)
                    await self._save_task(task)

        board.columns = new_columns
        board.updated_at = datetime.now(timezone.utc)
        await self._save_board(board)
        await self._emit_changed(summary=True)
        return {
            "id": board.id,
            "columns": [c.model_dump() for c in board.columns],
            "task_counter": board.task_counter,
        }

    async def anchor_summary(self) -> dict[str, Any]:
        await self._ensure_schema()
        board = await self._get_or_create_board()
        tasks = await self.repos.task_repo.get_all(doc_type="TaskSchema")
        done_columns = {c.id for c in board.columns if c.is_done}
        task_by_id = {t.id: t for t in tasks}

        open_tasks = [t for t in tasks if t.status not in done_columns]
        node_to_task_ids: dict[str, set[str]] = {}

        for task in open_tasks:
            closure_ids = self._closure_task_ids(task, task_by_id)
            anchor_node_ids: set[str] = set()
            for tid in closure_ids:
                for anchor in task_by_id[tid].anchors:
                    anchor_node_ids.add(anchor.node_id)
            for node_id in anchor_node_ids:
                node_to_task_ids.setdefault(node_id, set()).add(task.id)

        resolved_ids = await self._resolve_anchor_ids(set(node_to_task_ids.keys()))
        nodes: dict[str, dict[str, Any]] = {}
        hot_count = 0

        for node_id, task_ids in node_to_task_ids.items():
            if node_id not in resolved_ids:
                continue
            qname = await self._node_qname(node_id)
            open_count = len(task_ids)
            hot = open_count >= 2
            if hot:
                hot_count += 1
            nodes[node_id] = {
                "qname": qname,
                "open_task_ids": sorted(task_ids),
                "open_count": open_count,
                "hot": hot,
            }

        return {"nodes": nodes, "hot_count": hot_count}

    async def re_anchor_candidates(
        self,
        qname: str,
        kind: str | None = None,
    ) -> list[dict[str, str]]:
        await self._ensure_schema()
        seed = qname.split(".")[-1] if qname else qname
        candidates: list[dict[str, str]] = []
        seen: set[str] = set()

        for doc_type, node_kind in (
            ("FunctionSchema", "function"),
            ("ClassSchema", "class"),
            ("FileSchema", "file"),
            ("FolderSchema", "folder"),
        ):
            if kind and kind != node_kind:
                continue
            nodes = await self.repos.code_element_repo.get_all(doc_type=doc_type) \
                if doc_type in ("FunctionSchema", "ClassSchema") else []
            if doc_type == "FileSchema":
                nodes = await self.repos.structure_repo.get_all(doc_type="FileSchema")
            elif doc_type == "FolderSchema":
                nodes = await self.repos.structure_repo.get_all(doc_type="FolderSchema")

            for node in nodes:
                node_qname = getattr(node, "qname", None) or getattr(node, "name", "")
                if seed.lower() not in node_qname.lower():
                    continue
                if node.id in seen:
                    continue
                seen.add(node.id)
                candidates.append({
                    "node_id": node.id,
                    "qname": node_qname,
                    "kind": node_kind,
                })

        candidates.sort(
            key=lambda c: (
                0 if c["qname"].endswith(seed) else 1,
                c["qname"],
            ),
        )
        return candidates[:20]

    async def suggest_dependencies(self, node_id: str) -> list[dict[str, str]]:
        await self._ensure_schema()
        try:
            raw = await self.repos.client.get_document(node_id)
        except Exception:
            return []

        suggestions: list[dict[str, str]] = []
        seen: set[str] = set()

        def add(node_ref: Any, kind: str) -> None:
            if node_ref is None:
                return
            ref_id = node_ref if isinstance(node_ref, str) else node_ref.get("@id")
            if not ref_id or ref_id in seen:
                return
            seen.add(ref_id)
            suggestions.append({
                "node_id": ref_id,
                "qname": "",
                "kind": kind,
            })

        schema_type = node_id.split("/")[0] if "/" in node_id else ""

        for call_ref in raw.get("call_children") or []:
            call_id = call_ref if isinstance(call_ref, str) else call_ref.get("@id")
            if not call_id:
                continue
            try:
                call_raw = await self.repos.client.get_document(call_id)
            except Exception:
                continue
            target = call_raw.get("target_function") or call_raw.get("target_class")
            if target:
                target_id = target if isinstance(target, str) else target.get("@id")
                kind = "function" if call_raw.get("target_function") else "class"
                add(target_id, kind)

        if schema_type in ("FileSchema", "FolderSchema", "ClassSchema"):
            for fn_ref in raw.get("function_children") or []:
                add(fn_ref if isinstance(fn_ref, str) else fn_ref.get("@id"), "function")
            for cls_ref in raw.get("class_children") or []:
                add(cls_ref if isinstance(cls_ref, str) else cls_ref.get("@id"), "class")

        if schema_type == "FunctionSchema":
            for call_ref in raw.get("call_children") or []:
                call_id = call_ref if isinstance(call_ref, str) else call_ref.get("@id")
                if call_id:
                    try:
                        call_raw = await self.repos.client.get_document(call_id)
                        target = call_raw.get("target_function") or call_raw.get("target_class")
                        if target:
                            target_id = target if isinstance(target, str) else target.get("@id")
                            kind = "function" if call_raw.get("target_function") else "class"
                            add(target_id, kind)
                    except Exception:
                        pass

        for item in suggestions:
            if not item["qname"]:
                item["qname"] = await self._node_qname(item["node_id"])

        return suggestions[:12]

    # --- internals ---

    async def _get_or_create_board(self) -> BoardNode:
        board = await self.repos.board_repo.get_default()
        if board is not None:
            return self._normalize_board_columns(board)
        board = default_board_node()
        created = await self.repos.board_repo.create_nodes(
            board,
            singular_name="board",
            plural_name="boards",
        )
        if created is None:
            raise TaskServiceError("Failed to create board", 500)
        if isinstance(created, list):
            return created[0]
        return created

    async def _mint_key(self, board: BoardNode) -> str:
        board.task_counter += 1
        key = f"VN-{board.task_counter}"
        board.updated_at = datetime.now(timezone.utc)
        await self._save_board(board)
        return key

    async def _save_board(self, board: BoardNode) -> None:
        result = await self.repos.board_repo.update_node(
            board,
            commit_msg="Update board",
        )
        if result is None:
            raise TaskServiceError("Failed to save board", 500)

    async def _save_task(self, task: TaskNode) -> None:
        result = await self.repos.task_repo.update_node(
            task,
            commit_msg=f"task: {task.key} updated",
        )
        if result is None:
            raise TaskServiceError(f"Failed to save task {task.id}", 500)

    async def _get_task_or_raise(self, task_id: str) -> TaskNode:
        task = await self.repos.task_repo.get_by_id(task_id)
        if task is None:
            raise TaskServiceError(f"Task {task_id} not found", 404)
        return task

    async def _get_enriched_task(self, task_id: str) -> dict[str, Any]:
        payload = await self.get_board_payload()
        for task in payload["tasks"]:
            if task["id"] == task_id:
                return task
        raise TaskServiceError(f"Task {task_id} not found", 404)

    def _validate_column(self, board: BoardNode, column_id: str) -> None:
        ids = [c.id for c in board.columns]
        if column_id not in ids:
            raise TaskServiceError(
                f"Unknown column '{column_id}' — the board has: {', '.join(ids)}",
                422,
            )

    @staticmethod
    def _normalize_board_columns(board: BoardNode) -> BoardNode:
        normalized: list[BoardColumn] = []
        for col in board.columns:
            is_backlog = col.is_backlog or col.id == "backlog"
            normalized.append(
                col.model_copy(
                    update={
                        "is_backlog": is_backlog,
                        "is_done": False if is_backlog else col.is_done,
                    },
                ),
            )
        board.columns = normalized
        return board

    @staticmethod
    def _backlog_column(board: BoardNode) -> BoardColumn | None:
        for col in board.columns:
            if col.is_backlog:
                return col
        return None

    @staticmethod
    def _default_create_column_id(board: BoardNode) -> str:
        for col in board.columns:
            if not col.is_backlog and not col.is_done:
                return col.id
        for col in board.columns:
            if not col.is_backlog:
                return col.id
        return board.columns[0].id

    def _validate_board_columns_update(
        self,
        board: BoardNode,
        columns: list[dict[str, Any]],
    ) -> None:
        old_backlog = self._backlog_column(board)
        if old_backlog is None:
            return

        new_backlog_payload = next(
            (c for c in columns if c.get("id") == old_backlog.id),
            None,
        )
        if new_backlog_payload is None:
            raise TaskServiceError(
                f"'{old_backlog.title}' is the board's backlog column — "
                "it can be renamed, not deleted.",
                409,
            )

        if not new_backlog_payload.get("is_backlog", True):
            raise TaskServiceError(
                f"'{old_backlog.title}' is the board's backlog column — "
                "it can be renamed, not deleted.",
                409,
            )

        backlog_flags = sum(1 for c in columns if c.get("is_backlog"))
        if backlog_flags != 1:
            raise TaskServiceError(
                "The board must have exactly one backlog column.",
                409,
            )

        for col in columns:
            if col.get("is_backlog") and col.get("is_done"):
                raise TaskServiceError(
                    "A column cannot be both backlog and done.",
                    409,
                )

    async def _snapshot_anchor(self, node_id: str) -> TaskAnchor:
        try:
            raw = await self.repos.client.get_document(node_id)
        except Exception:
            raise TaskServiceError(
                f"{node_id} does not exist on this branch — pick a live node.",
                422,
            )
        schema_prefix = node_id.split("/")[0] if "/" in node_id else ""
        if schema_prefix == "CallSchema":
            target = raw.get("target_function") or raw.get("target_class")
            if not target:
                raise TaskServiceError(
                    "This call's target no longer exists on this branch — "
                    "anchor the function or class directly.",
                    422,
                )
            target_id = target if isinstance(target, str) else target.get("@id")
            return await self._snapshot_anchor(target_id)
        kind_map = {
            "FunctionSchema": "function",
            "ClassSchema": "class",
            "FileSchema": "file",
            "FolderSchema": "folder",
        }
        kind = kind_map.get(schema_prefix)
        if kind is None:
            raise TaskServiceError(
                f"{node_id} does not exist on this branch — pick a live node.",
                422,
            )
        qname = raw.get("qname") or raw.get("name") or node_id
        return TaskAnchor(node_id=node_id, qname=qname, kind=kind)

    async def _resolve_anchor_ids(self, node_ids: set[str]) -> set[str]:
        # TODO batch via WOQL when boards grow
        if not node_ids:
            return set()
        resolved: set[str] = set()
        for node_id in node_ids:
            try:
                await self.repos.client.get_document(node_id)
                resolved.add(node_id)
            except Exception:
                pass
        return resolved

    async def _node_qname(self, node_id: str) -> str:
        try:
            raw = await self.repos.client.get_document(node_id)
            return raw.get("qname") or raw.get("name") or node_id
        except Exception:
            return node_id

    async def _add_subtask_edge(self, parent: TaskNode, child_id: str) -> None:
        if child_id == parent.id:
            raise TaskServiceError(
                f"{parent.key} cannot be its own subtask.",
                409,
            )
        await self._validate_no_cycle(parent.id, child_id, edge="subtask")
        parent.subtask_ids.add(child_id)
        parent.updated_at = datetime.now(timezone.utc)
        await self._save_task(parent)

    async def _validate_no_cycle(
        self,
        from_id: str,
        to_id: str,
        *,
        edge: str,
    ) -> None:
        if from_id == to_id:
            from_task = await self.repos.task_repo.get_by_id(from_id)
            key = from_task.key if from_task else from_id
            raise TaskServiceError(f"{key} cannot link to itself.", 409)

        all_tasks = await self.repos.task_repo.get_all(doc_type="TaskSchema")
        task_by_id = {t.id: t for t in all_tasks}
        from_task = task_by_id.get(from_id)
        to_task = task_by_id.get(to_id)
        if not from_task or not to_task:
            return

        if edge == "subtask":
            if self._path_exists(to_id, from_id, task_by_id, "subtask_ids"):
                raise TaskServiceError(
                    f"{from_task.key} already contains {to_task.key} "
                    f"through the subtask graph — adding this edge would create a cycle.",
                    409,
                )
        else:
            if self._path_exists(to_id, from_id, task_by_id, "blocked_by_ids"):
                raise TaskServiceError(
                    f"{from_task.key} already contains {to_task.key} "
                    f"through blocked-by — adding this edge would create a cycle.",
                    409,
                )

    def _path_exists(
        self,
        start_id: str,
        target_id: str,
        task_by_id: dict[str, TaskNode],
        field: str,
    ) -> bool:
        visited: set[str] = set()
        stack = [start_id]
        while stack:
            current = stack.pop()
            if current == target_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            task = task_by_id.get(current)
            if not task:
                continue
            neighbors = getattr(task, field, set())
            stack.extend(neighbors)

    def _closure_task_ids(
        self,
        task: TaskNode,
        task_by_id: dict[str, TaskNode],
    ) -> set[str]:
        visited: set[str] = set()
        stack = [task.id]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            current_task = task_by_id.get(current)
            if not current_task:
                continue
            for child_id in current_task.subtask_ids:
                if child_id not in visited:
                    stack.append(child_id)
        return visited

    def _parent_count(self, task_id: str, task_by_id: dict[str, TaskNode]) -> int:
        return sum(1 for t in task_by_id.values() if task_id in t.subtask_ids)

    def _blocks_ids(self, task_id: str, task_by_id: dict[str, TaskNode]) -> list[str]:
        return sorted(
            t.id for t in task_by_id.values() if task_id in t.blocked_by_ids
        )

    def _subtask_progress(
        self,
        task: TaskNode,
        task_by_id: dict[str, TaskNode],
        done_columns: set[str],
    ) -> dict[str, int]:
        closure = self._closure_task_ids(task, task_by_id) - {task.id}
        if not closure:
            return {"done": 0, "total": 0}
        done = sum(
            1 for tid in closure if task_by_id[tid].status in done_columns
        )
        return {"done": done, "total": len(closure)}

    def _is_blocked(
        self,
        task: TaskNode,
        task_by_id: dict[str, TaskNode],
        done_columns: set[str],
    ) -> bool:
        for blocker_id in task.blocked_by_ids:
            blocker = task_by_id.get(blocker_id)
            if blocker and blocker.status not in done_columns:
                return True
        return False

    def _enrich_task(
        self,
        task: TaskNode,
        task_by_id: dict[str, TaskNode],
        done_columns: set[str],
        resolved_ids: set[str],
    ) -> dict[str, Any]:
        anchors = [
            {
                **a.model_dump(),
                "is_resolved": a.node_id in resolved_ids,
            }
            for a in task.anchors
        ]
        subtasks = [
            {
                "id": child_id,
                "key": task_by_id[child_id].key,
                "title": task_by_id[child_id].name,
                "status": task_by_id[child_id].status,
                "shared": self._parent_count(child_id, task_by_id) > 1,
            }
            for child_id in task.subtask_ids
            if child_id in task_by_id
        ]
        return {
            "id": task.id,
            "key": task.key,
            "title": task.name,
            "description": task.description,
            "task_type": task.task_type,
            "status": task.status,
            "priority": task.priority,
            "labels": sorted(task.labels),
            "rank": task.rank,
            "anchors": anchors,
            "subtasks": subtasks,
            "blocked_by": [
                {
                    "id": bid,
                    "key": task_by_id[bid].key,
                    "title": task_by_id[bid].name,
                    "status": task_by_id[bid].status,
                }
                for bid in task.blocked_by_ids
                if bid in task_by_id
            ],
            "blocks": [
                {
                    "id": bid,
                    "key": task_by_id[bid].key,
                    "title": task_by_id[bid].name,
                    "status": task_by_id[bid].status,
                }
                for bid in self._blocks_ids(task.id, task_by_id)
                if bid in task_by_id
            ],
            "notes": [n.model_dump(mode="json") for n in task.notes],
            "blocked": self._is_blocked(task, task_by_id, done_columns),
            "subtask_progress": self._subtask_progress(
                task, task_by_id, done_columns
            ),
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }

    def _rank_at_top(self, tasks: list[TaskNode], column_id: str) -> str:
        column_tasks = sorted(
            [t for t in tasks if t.status == column_id],
            key=lambda t: t.rank,
        )
        if not column_tasks:
            return RANK_MID
        return mid_rank(None, column_tasks[0].rank)


def mid_rank(left: str | None, right: str | None) -> str:
    if left is None and right is None:
        return RANK_MID
    if left is None:
        left = RANK_MIN
    if right is None:
        right = RANK_MAX

    result = []
    i = 0
    while True:
        left_char = left[i] if i < len(left) else RANK_MIN
        right_char = right[i] if i < len(right) else RANK_MAX
        if left_char == right_char:
            result.append(left_char)
            i += 1
            if i > max(len(left), len(right)) + 8:
                return "".join(result) + RANK_MID
            continue
        left_idx = RANK_ALPHABET.index(left_char)
        right_idx = RANK_ALPHABET.index(right_char)
        if right_idx - left_idx > 1:
            mid_idx = (left_idx + right_idx) // 2
            result.append(RANK_ALPHABET[mid_idx])
            return "".join(result)
        result.append(left_char)
        i += 1
