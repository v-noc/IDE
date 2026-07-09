from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.walkthrough.loader import _fetch_node


@pytest.mark.asyncio
async def test_fetch_node_routes_code_element_group_to_group_repo():
    repos = MagicMock()
    repos.code_element_group_repo.get_by_id = AsyncMock(return_value="group-node")
    repos.structure_repo.get_by_id = AsyncMock()

    node_id = "CodeElementGroupSchema/abc123"
    result = await _fetch_node(repos, node_id)

    repos.code_element_group_repo.get_by_id.assert_awaited_once_with(node_id)
    repos.structure_repo.get_by_id.assert_not_awaited()
    assert result == "group-node"


@pytest.mark.asyncio
async def test_fetch_node_routes_call_group_to_call_group_repo():
    repos = MagicMock()
    repos.call_group_repo.get_by_id = AsyncMock(return_value="call-group-node")
    repos.structure_repo.get_by_id = AsyncMock()

    node_id = "CallGroupSchema/xyz"
    result = await _fetch_node(repos, node_id)

    repos.call_group_repo.get_by_id.assert_awaited_once_with(node_id)
    repos.structure_repo.get_by_id.assert_not_awaited()
    assert result == "call-group-node"
