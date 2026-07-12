import pytest

from app.walkthrough.graph import GraphNode, build_graph, expand_children, sort_children_by_source


def test_build_graph_from_domain_style_nodes():
    class FakeNode:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    raw = FakeNode(
        id="FunctionSchema/f",
        name="charge",
        qname="charge",
        description="fn",
        children={"CallSchema/c"},
        code_position=type("P", (), {"line_no": 10, "end_line_no": 20})(),
    )
    graph = build_graph("FunctionSchema/f", [raw])
    assert "FunctionSchema/f" in graph
    assert graph["FunctionSchema/f"].line_no == 10


def test_expand_children_skips_groups():
    graph = {
        "fn": GraphNode("fn", "fn", "fn", "function", "", ["grp"]),
        "grp": GraphNode("grp", "g", None, "group", "", ["child"]),
        "child": GraphNode("child", "child", "child", "function", "", []),
    }
    assert expand_children(graph, "fn") == ["child"]


def test_sort_children_by_source_line():
    graph = {
        "p": GraphNode("p", "p", "p", "function", "", ["b", "a"]),
        "a": GraphNode("a", "a", "a", "call", "", [], line_no=20),
        "b": GraphNode("b", "b", "b", "call", "", [], line_no=5),
    }
    ordered = sort_children_by_source(graph, ["b", "a"])
    assert ordered == ["b", "a"]
