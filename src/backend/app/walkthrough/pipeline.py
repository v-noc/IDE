from __future__ import annotations

from app.agent.llm.structured import structured_call
from app.core.services.code_element_service import CodeElementService
from app.walkthrough.context import NodeContext, build_context
from app.walkthrough.prompts import (
    block_plan_system_prompt,
    block_plan_user_prompt,
    block_text_system_prompt,
    block_text_user_prompt,
    intro_system_prompt,
    intro_user_prompt,
)
from app.walkthrough.fallbacks import (
    block_text_fallback,
    even_split_plan,
    intro_fallback,
    single_block_plan,
)
from app.walkthrough.patcher import Patcher
from app.walkthrough.schemas import (
    BlockPlan,
    BlockStep,
    BlockTextOut,
    IntroOut,
    VisitList,
    VisitNode,
    WalkthroughSession,
)
from app.walkthrough.validators import validate_block_plan


def _numbered_code(code: str, start_line: int) -> str:
    lines = code.splitlines()
    parts = []
    for index, line in enumerate(lines):
        line_no = start_line + index
        parts.append(f"{line_no:4d} | {line}")
    return "\n".join(parts)


async def _load_numbered_code(
    code_service: CodeElementService,
    visit: VisitNode,
) -> str | None:
    if not visit.has_code or visit.start_line is None:
        return None
    code_node_id = (
        visit.target_id
        if visit.node_type == "call" and visit.target_id
        else visit.node_id
    )
    payload = await code_service.get_code(code_node_id)
    if not payload or not payload.get("code"):
        return None
    return _numbered_code(payload["code"], visit.start_line)


async def run_pipeline(
    session: WalkthroughSession,
    patcher: Patcher,
    *,
    code_service: CodeElementService,
) -> WalkthroughSession:
    visit_list = session.visit_list
    error_log = list(session.error_log)

    for visit in visit_list.nodes:
        await patcher.open_node_steps(visit.order, visit.node_id, visit.mode)

        ctx = build_context(visit, visit_list_len=len(visit_list.nodes))
        numbered_code = await _load_numbered_code(code_service, visit)
        ctx.numbered_code = numbered_code

        intro_result, intro_errors = await structured_call(
            "intro",
            IntroOut,
            intro_system_prompt(ctx),
            intro_user_prompt(ctx),
        )
        error_log.extend(intro_errors)
        intro_degraded = intro_result is None
        intro_text = (
            intro_result.intro if intro_result else intro_fallback(visit)
        )
        await patcher.set_intro(visit.order, intro_text, intro_degraded)

        if visit.mode == "contextual" or not visit.has_code:
            continue

        plan: BlockPlan
        plan_degraded = False

        if not visit.gated:
            plan = single_block_plan(visit)
        elif numbered_code is None:
            plan_degraded = True
            min_blocks, max_blocks = ctx.min_blocks, ctx.max_blocks
            error_log.append(f"code unavailable for {visit.node_id}")
            plan = even_split_plan(
                visit.start_line or 1,
                visit.end_line or (visit.start_line or 1),
                min_blocks=min_blocks,
                max_blocks=max_blocks,
            )
        else:
            plan_ctx = build_context(
                visit,
                visit_list_len=len(visit_list.nodes),
                numbered_code=numbered_code,
            )
            plan_result, plan_errors = await structured_call(
                "block_plan",
                BlockPlan,
                block_plan_system_prompt(),
                block_plan_user_prompt(plan_ctx),
                validate=lambda result: validate_block_plan(result, visit),
            )
            error_log.extend(plan_errors)
            if plan_result is None:
                plan_degraded = True
                min_blocks, max_blocks = plan_ctx.min_blocks, plan_ctx.max_blocks
                plan = even_split_plan(
                    visit.start_line or 1,
                    visit.end_line or (visit.start_line or 1),
                    min_blocks=min_blocks,
                    max_blocks=max_blocks,
                )
            else:
                plan = plan_result

        previous_focus: list[str] = []
        for index, block in enumerate(plan.blocks):
            await patcher.add_block(
                visit.order,
                BlockStep(
                    index=index,
                    start_line=block.start_line,
                    end_line=block.end_line,
                    focus=block.focus,
                    text="",
                    degraded=plan_degraded,
                ),
            )

            text_ctx = _block_text_context(
                visit,
                visit_list,
                numbered_code,
                block.focus,
                block.start_line,
                block.end_line,
                previous_focus,
            )
            text_result, text_errors = await structured_call(
                "block_text",
                BlockTextOut,
                block_text_system_prompt(),
                block_text_user_prompt(text_ctx),
            )
            error_log.extend(text_errors)
            text_degraded = text_result is None or plan_degraded
            block_text = (
                text_result.text if text_result else block_text_fallback(block.focus)
            )
            await patcher.set_block_text(
                visit.order,
                index,
                block_text,
                text_degraded,
            )
            previous_focus.append(block.focus)

    session = patcher.mirror.model_copy(deep=True)
    session.error_log = error_log
    return session


def _block_text_context(
    visit: VisitNode,
    visit_list: VisitList,
    numbered_code: str | None,
    block_focus: str,
    block_start: int,
    block_end: int,
    previous_focus: list[str],
) -> NodeContext:
    ctx = build_context(visit, visit_list_len=len(visit_list.nodes))
    ctx.numbered_code = numbered_code
    ctx.block_focus = block_focus
    ctx.block_start = block_start
    ctx.block_end = block_end
    ctx.previous_focus_lines = list(previous_focus)
    return ctx
