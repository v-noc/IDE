from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.walkthrough.pipeline import _load_numbered_code
from app.walkthrough.schemas import VisitNode


@pytest.mark.asyncio
async def test_load_numbered_code_uses_call_target():
    code_service = AsyncMock()
    code_service.get_code = AsyncMock(return_value={"code": "return 1\n"})

    visit = VisitNode(
        node_id="call-1",
        name="helper",
        qname=None,
        node_type="call",
        description="",
        level=1,
        order=1,
        parent_order=0,
        target_id="target-fn",
        mode="full",
        first_seen_order=None,
        has_code=True,
        start_line=5,
        end_line=8,
        line_count=4,
        gated=False,
    )

    result = await _load_numbered_code(code_service, visit)

    code_service.get_code.assert_awaited_once_with("target-fn")
    assert result is not None
    assert "5 |" in result
