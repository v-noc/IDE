from __future__ import annotations

from typing import Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from app.agent.llm.structured import structured_call
from app.walkthrough.context import trim_for_intro, with_block_fields
from app.walkthrough.fallbacks import (
    block_text_fallback,
    even_split_plan,
    intro_fallback,
    single_block_plan,
)
from app.walkthrough.pipeline import _load_numbered_code, _record_errors
from app.walkthrough.prompts import (
    block_plan_system_prompt,
    block_plan_user_prompt,
    block_text_system_prompt,
    block_text_user_prompt,
    intro_system_prompt,
    intro_user_prompt,
)
from app.walkthrough.schemas import BlockPlan, BlockStep, BlockTextOut, IntroOut
from app.walkthrough.validators import validate_block_plan


class WalkState(TypedDict):
    cursor: int
    total: int
    stop_mode: str
    stop_has_code: bool
    stop_gated: bool
    plan: BlockPlan | None
    plan_degraded: bool
    block_cursor: int


def _cfg(config: RunnableConfig) -> dict[str, Any]:
    return config["configurable"]  # type: ignore[index]


def make_initial_state(total: int) -> WalkState:
    return WalkState(
        cursor=0,
        total=total,
        stop_mode="",
        stop_has_code=False,
        stop_gated=False,
        plan=None,
        plan_degraded=False,
        block_cursor=0,
    )


async def intro_node(state: WalkState, config: RunnableConfig) -> dict[str, Any]:
    cfg = _cfg(config)
    visit = cfg["visit_list"].nodes[state["cursor"]]
    patcher = cfg["patcher"]
    code_service = cfg["code_service"]
    contexts = cfg["contexts"]
    errors = cfg["errors"]

    await patcher.open_node_steps(visit.order, visit.node_id, visit.mode)

    ctx = contexts[visit.order]
    numbered_code = await _load_numbered_code(code_service, visit)
    ctx.numbered_code = numbered_code
    if numbered_code is not None and visit.end_line is not None:
        ctx.intro_code = trim_for_intro(numbered_code, visit.end_line)
    else:
        ctx.intro_code = numbered_code

    verbosity = cfg.get("verbosity", "normal")
    user_query = cfg.get("user_query", "")

    intro_result, intro_errors = await structured_call(
        "intro",
        IntroOut,
        intro_system_prompt(ctx, verbosity),
        intro_user_prompt(ctx, user_query),
    )
    await _record_errors(patcher, errors, intro_errors)
    intro_degraded = intro_result is None
    intro_text = intro_result.intro if intro_result else intro_fallback(visit)
    await patcher.set_intro(visit.order, intro_text, intro_degraded)

    return {
        "stop_mode": visit.mode,
        "stop_has_code": visit.has_code,
        "stop_gated": visit.gated,
        "plan": None,
        "plan_degraded": False,
        "block_cursor": 0,
    }


async def single_block_node(state: WalkState, config: RunnableConfig) -> dict[str, Any]:
    visit = _cfg(config)["visit_list"].nodes[state["cursor"]]
    return {
        "plan": single_block_plan(visit),
        "plan_degraded": False,
    }


async def block_plan_node(state: WalkState, config: RunnableConfig) -> dict[str, Any]:
    cfg = _cfg(config)
    visit = cfg["visit_list"].nodes[state["cursor"]]
    patcher = cfg["patcher"]
    contexts = cfg["contexts"]
    errors = cfg["errors"]
    ctx = contexts[visit.order]
    numbered_code = ctx.numbered_code

    if numbered_code is None:
        min_blocks, max_blocks = ctx.min_blocks, ctx.max_blocks
        await _record_errors(
            patcher,
            errors,
            [f"code unavailable for {visit.node_id}"],
        )
        return {
            "plan": even_split_plan(
                visit.start_line or 1,
                visit.end_line or (visit.start_line or 1),
                min_blocks=min_blocks,
                max_blocks=max_blocks,
            ),
            "plan_degraded": True,
        }

    plan_result, plan_errors = await structured_call(
        "block_plan",
        BlockPlan,
        block_plan_system_prompt(ctx),
        block_plan_user_prompt(ctx),
        validate=lambda result: validate_block_plan(result, visit),
    )
    await _record_errors(patcher, errors, plan_errors)
    if plan_result is None:
        min_blocks, max_blocks = ctx.min_blocks, ctx.max_blocks
        return {
            "plan": even_split_plan(
                visit.start_line or 1,
                visit.end_line or (visit.start_line or 1),
                min_blocks=min_blocks,
                max_blocks=max_blocks,
            ),
            "plan_degraded": True,
        }
    return {"plan": plan_result, "plan_degraded": False}


async def explain_block_node(state: WalkState, config: RunnableConfig) -> dict[str, Any]:
    cfg = _cfg(config)
    visit = cfg["visit_list"].nodes[state["cursor"]]
    patcher = cfg["patcher"]
    contexts = cfg["contexts"]
    errors = cfg["errors"]
    ctx = contexts[visit.order]
    plan = state["plan"]
    assert plan is not None

    index = state["block_cursor"]
    block = plan.blocks[index]
    plan_degraded = state["plan_degraded"]

    await patcher.add_block(
        visit.order,
        BlockStep(
            index=index,
            start_line=block.start_line,
            end_line=block.end_line,
            focus=block.focus,
            description=block.description,
            text="",
            degraded=plan_degraded,
        ),
    )

    previous_block_lines = [
        f"lines {b.start_line}-{b.end_line}: {b.focus} — {b.description}"
        for b in plan.blocks[:index]
    ]
    text_ctx = with_block_fields(
        ctx,
        block_focus=block.focus,
        block_description=block.description,
        block_start=block.start_line,
        block_end=block.end_line,
        previous_block_lines=previous_block_lines,
    )
    verbosity = cfg.get("verbosity", "normal")
    user_query = cfg.get("user_query", "")

    text_result, text_errors = await structured_call(
        "block_text",
        BlockTextOut,
        block_text_system_prompt(text_ctx, verbosity),
        block_text_user_prompt(text_ctx, user_query),
    )
    await _record_errors(patcher, errors, text_errors)
    text_degraded = text_result is None or plan_degraded
    block_text = text_result.text if text_result else block_text_fallback(block.focus)
    await patcher.set_block_text(
        visit.order,
        index,
        block_text,
        text_degraded,
    )

    return {"block_cursor": index + 1}


async def advance_node(state: WalkState, config: RunnableConfig) -> dict[str, Any]:
    return {"cursor": state["cursor"] + 1}


def route_after_intro(state: WalkState) -> str:
    if state["stop_mode"] == "contextual" or not state["stop_has_code"]:
        return "advance"
    return "block_plan" if state["stop_gated"] else "single_block"


def route_after_explain(state: WalkState) -> str:
    assert state["plan"] is not None
    if state["block_cursor"] < len(state["plan"].blocks):
        return "explain_block"
    return "advance"


def route_after_advance(state: WalkState) -> str:
    if state["cursor"] < state["total"]:
        return "intro"
    return END


def _build_graph():
    builder = StateGraph(WalkState)
    builder.add_node("intro", intro_node)
    builder.add_node("single_block", single_block_node)
    builder.add_node("block_plan", block_plan_node)
    builder.add_node("explain_block", explain_block_node)
    builder.add_node("advance", advance_node)

    builder.add_edge(START, "intro")
    builder.add_conditional_edges("intro", route_after_intro)
    builder.add_edge("single_block", "explain_block")
    builder.add_edge("block_plan", "explain_block")
    builder.add_conditional_edges("explain_block", route_after_explain)
    builder.add_conditional_edges("advance", route_after_advance)

    return builder.compile()


GRAPH = _build_graph()
