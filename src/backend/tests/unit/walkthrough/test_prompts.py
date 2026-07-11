from __future__ import annotations

from app.walkthrough.context import NodeContext
from app.walkthrough.prompts import (
    GLOSSARY,
    block_plan_system_prompt,
    block_plan_user_prompt,
    block_text_system_prompt,
    intro_system_prompt,
    intro_user_prompt,
)


def _ctx(**kwargs) -> NodeContext:
    base = dict(
        node_id="fn",
        header="function charge — PaymentService.charge",
        description="charges a card",
        docs_excerpt="",
        parent_line="",
        child_lines=[],
        caller_line=None,
        first_seen_ref=None,
        numbered_code="  10 | def charge():\n  11 |     return 1",
        intro_code="  10 | def charge():\n  11 |     return 1",
        tour_position="stop 1 of 3",
        node_type="function",
        mode="full",
        min_blocks=2,
        max_blocks=4,
        start_line=10,
        end_line=50,
    )
    base.update(kwargs)
    return NodeContext(**base)


def test_glossary_in_every_system_prompt():
    assert "code-element group" in GLOSSARY
    ctx = _ctx()
    for system in (
        intro_system_prompt(ctx),
        intro_system_prompt(_ctx(mode="contextual")),
        block_plan_system_prompt(ctx),
        block_text_system_prompt(
            _ctx(block_start=10, block_end=20, block_focus="x"),
        ),
    ):
        assert "code-element group" in system


def test_json_word_in_every_system_prompt():
    ctx = _ctx()
    for system in (
        intro_system_prompt(ctx),
        intro_system_prompt(_ctx(mode="contextual")),
        block_plan_system_prompt(ctx),
        block_text_system_prompt(
            _ctx(block_start=10, block_end=20, block_focus="x"),
        ),
    ):
        assert "JSON" in system


def test_block_text_filters_names_in_range():
    from app.walkthrough.prompts import block_text_user_prompt

    ctx = _ctx(
        block_start=10,
        block_end=20,
        block_focus="validate",
        block_description="Checks input.",
        child_line_entries=[
            (5, "· early (function) — before block"),
            (15, "· in_range (function) — inside block"),
            (50, "· late (function) — after block"),
        ],
    )
    user = block_text_user_prompt(ctx)
    assert "in_range" in user
    assert "early" not in user
    assert "late" not in user
    assert "### names in this block" in user

    out_of_range = _ctx(
        block_start=10,
        block_end=20,
        block_focus="validate",
        block_description="Checks input.",
        child_line_entries=[(50, "· late (function) — after block")],
    )
    assert "### names in this block" not in block_text_user_prompt(out_of_range)


def test_intro_omits_empty_docs_section():
    user = intro_user_prompt(_ctx(docs_excerpt=""))
    assert "### documentation" not in user
    assert "### code" in user


def test_intro_includes_docs_and_code():
    user = intro_user_prompt(
        _ctx(docs_excerpt="### doc: Overview\nDoes charging."),
    )
    assert "### documentation" in user
    assert "### code" in user


def test_block_plan_system_quotes_bounds():
    system = block_plan_system_prompt(_ctx(min_blocks=2, max_blocks=5))
    assert "2-5" in system
    user = block_plan_user_prompt(_ctx(min_blocks=2, max_blocks=5))
    assert "Split into 2-5 blocks now." in user
