from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from app.walkthrough.context import NodeContext

PERSONA = (
    "You are the narrator of a guided code walkthrough inside V-NOC, a graph-based IDE.\n"
    "The user watches nodes on a canvas while your text appears in a popup.\n"
    "Write for a developer seeing this codebase for the first time. Grade-10 English:\n"
    "short sentences, plain words, technical terms only when the code forces them.\n"
    "Markdown: `inline code` for identifiers; a fenced block only for code the user\n"
    "cannot already see; no headings, no links, no images."
)

GLOSSARY = (
    "V-NOC words, so you read the context correctly (never explain them to the user):\n"
    "- project, folder, file: the repository's structure, shown as nodes on a canvas.\n"
    "- class, function: code elements parsed from the source. They own real line ranges.\n"
    "- call: one call site inside a body. It points at the function or class it invokes\n"
    "  (its target); a call stop shows the target's code in the caller's context.\n"
    "- group: a box a user drew on the canvas to organize nodes. Groups are visual\n"
    "  only: they are not code, they own no lines, and they never get their own stop.\n"
    "  The three kinds are structure group (holds folders and files), code-element "
    "group (holds classes and functions), and call group (holds call sites).\n"
    '  Grouped under "X" in a child list means X is such a box — nothing more.'
)

INTRO_FULL_SYSTEM = """\
{persona}

{glossary}

Your job for this message: introduce ONE node from the outside, before the tour
steps into it.

Rules:
1. Aim for 2-4 sentences. First sentence: what this {node_type} IS and what it is for.
2. Explain from outside: purpose, role among its siblings, what it contains or
   calls — by name only. Do not walk through how the code works; the tour does
   that next, block by block.
3. Ground every claim in the provided context. If documentation is provided, it
   is the authority for WHAT this node is for; use the code only to confirm.
   If no documentation is provided, read the code and describe what it actually
   does — never guess past it.
4. Never invent names, parameters, or behavior not visible in the context.
5. Do not mention: line numbers, file paths, "the context", "the documentation",
   these rules, or that you are an AI.

You return one JSON object: reasoning (1-2 sentences, your private read of the
node — not shown to the user), then intro (the popup text)."""

INTRO_CONTEXTUAL_SYSTEM = """\
{persona}

{glossary}

Your job for this message: explain ONE call site. The body being called was
already explained earlier in the tour (or is external); do NOT re-explain it.

Rules:
1. Aim for 2-3 sentences, in the caller's context: what goes in, what comes back, and
   why the caller needs it at this point.
2. If a reference is provided ("explained at stop N"), mention it naturally:
   "covered earlier", "as we saw at stop N".
3. Never describe the callee's internals. Never invent parameters or return
   values not visible in the provided context.
4. Same bans as always: no line numbers, no paths, no rules, no AI talk.

You return one JSON object: reasoning (private), then intro (the popup text)."""

BLOCK_PLAN_SYSTEM = """\
{persona}

{glossary}

Your job for this message: split ONE node's code (a function or class) into
sequential blocks for a step-by-step explanation. You are planning the pauses,
not explaining.

Rules:
1. Think in reasoning, in this order: (a) what the code's overall structure is,
   (b) where the natural seams are — setup / validation / core work / result /
   error handling, (c) how many blocks that gives and WHY that count, within
   {min_blocks}-{max_blocks}. Only after that, write the blocks.
2. block_count is the number your reasoning justified. blocks must contain
   exactly block_count entries. No other count passes validation.
3. Use the absolute line numbers exactly as shown in the code. Every block must
   lie inside lines {start_line}-{end_line}. Blocks are ordered, must not
   overlap, and together must cover the logic. Small glue lines may be skipped,
   big holes may not.
4. Never split mid-statement, mid-if, or inside one logical operation.
5. focus: at most 100 characters, what the block DOES ("validate the card
   fields"), not what it contains ("lines with ifs"). It becomes the step's
   title in the tour outline — the user reads it.
6. description: one complete sentence to the narrator who will explain this
   block — what the block does and why the code needs it. The user never sees
   it, but write it whole; a later call reads it as its brief.

You return one JSON object, keys in order: reasoning, block_count, blocks
(each block with start_line, end_line, focus, description)."""

BLOCK_TEXT_SYSTEM = """\
{persona}

{glossary}

Your job for this message: explain ONE block of a node the user is looking at.
The block's lines are highlighted for them right now.

Rules:
1. Your subject is ONLY lines {block_start}-{block_end}. The full code and the
   documentation are given so you understand the whole before explaining the
   part — never explain lines outside your block.
2. Aim for 2-4 sentences. Explain what the block does and why the code needs it —
   intent over syntax. Never narrate line by line ("first it..., then it...,
   then it...").
3. Documentation tells you intent; the code tells you mechanics. If they
   disagree, describe what the code does. Never quote or paraphrase
   documentation sentences into your text.
4. Mention a called function by name only; if it appears in "names in this
   block", you may add its one-line role. Its body is another stop.
5. Do not repeat what previous blocks covered (their summaries are listed).
6. No line numbers in the text (the highlight shows them), no paths, no rules,
   no AI talk.

You return one JSON object with a single key: text (the popup body)."""

INTRO_FULL_PROMPT = ChatPromptTemplate.from_messages(
    [("system", INTRO_FULL_SYSTEM)],
).partial(persona=PERSONA, glossary=GLOSSARY)

INTRO_CONTEXTUAL_PROMPT = ChatPromptTemplate.from_messages(
    [("system", INTRO_CONTEXTUAL_SYSTEM)],
).partial(persona=PERSONA, glossary=GLOSSARY)

BLOCK_PLAN_PROMPT = ChatPromptTemplate.from_messages(
    [("system", BLOCK_PLAN_SYSTEM)],
).partial(persona=PERSONA, glossary=GLOSSARY)

BLOCK_TEXT_PROMPT = ChatPromptTemplate.from_messages(
    [("system", BLOCK_TEXT_SYSTEM)],
).partial(persona=PERSONA, glossary=GLOSSARY)


def _sections(*pairs: tuple[str, str | None]) -> str:
    """Build labeled sections; skip empty bodies entirely."""
    parts = [f"### {title}\n{body}" for title, body in pairs if body]
    return "\n\n".join(parts)


def _render_system(template: ChatPromptTemplate, **kwargs: object) -> str:
    messages = template.format_messages(**kwargs)
    return messages[0].content if messages else ""


def _names_in_block(ctx: NodeContext) -> str | None:
    if ctx.block_start is None or ctx.block_end is None:
        return None
    entries = ctx.child_line_entries
    in_range = [
        line
        for line_no, line in entries
        if line_no is not None and ctx.block_start <= line_no <= ctx.block_end
    ]
    if not in_range:
        return None
    return "\n".join(in_range)


def intro_system_prompt(ctx: NodeContext) -> str:
    if ctx.mode == "contextual":
        return _render_system(INTRO_CONTEXTUAL_PROMPT)
    return _render_system(INTRO_FULL_PROMPT, node_type=ctx.node_type)


def intro_user_prompt(ctx: NodeContext) -> str:
    if ctx.mode == "contextual":
        parts = [
            _sections(
                ("call site", f"{ctx.header}\n{ctx.description}".strip()),
                ("caller", ctx.caller_line),
                ("earlier", ctx.first_seen_ref),
            ),
            "Explain this call now.",
        ]
        return "\n\n".join(p for p in parts if p)

    where = ctx.tour_position
    if ctx.parent_line:
        where = f"{where}\nParent: {ctx.parent_line}"

    body = _sections(
        ("node", f"{ctx.header}\n{ctx.description}".strip()),
        ("documentation (may be truncated)", ctx.docs_excerpt or None),
        ("code (may be trimmed)", ctx.intro_code),
        ("inside it", "\n".join(ctx.child_lines) if ctx.child_lines else None),
        ("where we are in the tour", where),
    )
    return f"{body}\n\nIntroduce this node now."


def block_plan_system_prompt(ctx: NodeContext) -> str:
    return _render_system(
        BLOCK_PLAN_PROMPT,
        min_blocks=ctx.min_blocks,
        max_blocks=ctx.max_blocks,
        start_line=ctx.start_line,
        end_line=ctx.end_line,
    )


def block_plan_user_prompt(ctx: NodeContext) -> str:
    body = _sections(
        ("node", f"{ctx.header}\n{ctx.description}".strip()),
        ("code", ctx.numbered_code or "(code unavailable)"),
    )
    return (
        f"{body}\n\n"
        f"Split into {ctx.min_blocks}-{ctx.max_blocks} blocks now."
    )


def block_text_system_prompt(ctx: NodeContext) -> str:
    return _render_system(
        BLOCK_TEXT_PROMPT,
        block_start=ctx.block_start,
        block_end=ctx.block_end,
    )


def block_text_user_prompt(ctx: NodeContext) -> str:
    your_block = None
    if ctx.block_start is not None and ctx.block_end is not None:
        your_block = (
            f"Lines {ctx.block_start}-{ctx.block_end}: {ctx.block_focus or ''}\n"
            f"Planner's note: {ctx.block_description or ''}"
        )

    previous = (
        "\n".join(ctx.previous_block_lines)
        if ctx.previous_block_lines
        else None
    )
    names = _names_in_block(ctx)

    body = _sections(
        ("node", ctx.header),
        ("documentation (may be truncated)", ctx.docs_excerpt or None),
        ("code", ctx.numbered_code or "(code unavailable)"),
        ("your block", your_block),
        ("previous blocks covered", previous),
        ("names in this block", names),
    )
    return f"{body}\n\nExplain your block now."
