from __future__ import annotations

from app.walkthrough.context import NodeContext

PERSONA = (
    "You are the narrator of a guided code walkthrough inside V-NOC, a graph-based IDE. "
    "The user is watching the code on a canvas while your text appears in a popup. "
    "Write for a developer seeing this codebase for the first time."
)


def intro_system_prompt(ctx: NodeContext) -> str:
    variant = (
        "introduce ONE node from the outside"
        if ctx.mode == "full"
        else "explain what this call does for its caller"
    )
    return (
        f"{PERSONA}\n\nYour job: {variant}.\n"
        "Return reasoning first, then intro (2-4 sentences)."
    )


def intro_user_prompt(ctx: NodeContext) -> str:
    parts = [
        "### node",
        ctx.header,
        ctx.description,
        "",
        f"### tour\n{ctx.tour_position}",
    ]
    if ctx.first_seen_ref:
        parts.extend(["", f"### reference\n{ctx.first_seen_ref}"])
    return "\n".join(parts)


def block_plan_system_prompt() -> str:
    return (
        f"{PERSONA}\n\nYour job: split the node's code into logical blocks. "
        "Return reasoning first, then blocks with start_line, end_line, focus."
    )


def block_plan_user_prompt(ctx: NodeContext) -> str:
    return "\n".join(
        [
            "### node",
            ctx.header,
            "",
            f"Choose between {ctx.min_blocks} and {ctx.max_blocks} blocks.",
            f"The function spans lines {ctx.start_line}–{ctx.end_line}.",
            "",
            "### code",
            ctx.numbered_code or "(code unavailable)",
        ],
    )


def block_text_system_prompt() -> str:
    return (
        f"{PERSONA}\n\nYour job: explain ONE block of code in 2-4 sentences. "
        "Return a single text field."
    )


def block_text_user_prompt(ctx: NodeContext) -> str:
    parts = [
        "### node",
        ctx.header,
        "",
        "### code",
        ctx.numbered_code or "(code unavailable)",
        "",
        "### this block",
        (
            f"Lines {ctx.block_start}-{ctx.block_end}: {ctx.block_focus}"
            if ctx.block_start is not None and ctx.block_end is not None
            else (ctx.block_focus or "this section")
        ),
    ]
    if ctx.previous_focus_lines:
        parts.extend(["", "### previous blocks", *ctx.previous_focus_lines])
    return "\n".join(parts)
