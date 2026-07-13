import pytest

from app.walkthrough.depth import subtree_max_depth
from app.walkthrough.graph import GraphNode


@pytest.mark.asyncio
async def test_subtree_max_depth_bfs_levels(monkeypatch):
    parent = GraphNode(
        id="FunctionSchema/root",
        name="root",
        qname=None,
        kind="function",
        description="root",
        children=["FunctionSchema/child"],
    )
    child = GraphNode(
        id="FunctionSchema/child",
        name="child",
        qname=None,
        kind="function",
        description="child",
        children=["FunctionSchema/leaf"],
        parent_id="FunctionSchema/root",
    )
    leaf = GraphNode(
        id="FunctionSchema/leaf",
        name="leaf",
        qname=None,
        kind="function",
        description="leaf",
        parent_id="FunctionSchema/child",
    )
    graph = {parent.id: parent, child.id: child, leaf.id: leaf}

    async def fake_load(repos, node_id, depth_max=None):
        return graph

    monkeypatch.setattr(
        "app.walkthrough.depth.load_traversal_graph",
        fake_load,
    )

    depth = await subtree_max_depth(
        None, "FunctionSchema/root", hard_cap=5,  # type: ignore[arg-type]
    )
    assert depth == 2
