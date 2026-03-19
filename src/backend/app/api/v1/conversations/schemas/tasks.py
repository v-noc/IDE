from __future__ import annotations

from typing import Any


def task_to_wire(t: Any) -> dict[str, Any]:
    return t.model_dump(mode="json")


def subtask_to_wire(st: Any) -> dict[str, Any]:
    return st.model_dump(mode="json")
