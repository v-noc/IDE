# 14 — Prompts & Context Upgrade (PROMPT_VERSION "2", SCHEMA_VERSION "2")

> Implements the 2026-07-11 revision of plan docs `04-data-types.md`,
> `06-context-engineering.md`, `07-prompting.md`, `08-chain-of-thought.md` and
> `backend/02-llm-provider.md`. **07 Part 2 and 06 are canonical** — the prompt texts
> and the context table live there; this doc tells you where they land in code and in
> what order to change things. Read both before touching anything.

Follow the README ground rules: open every file before editing, find code by
searching for the quoted snippet, one step at a time, verify by running.

## What this fix delivers (summary)

| Change | Plan doc |
|---|---|
| GLOSSARY layer (node kinds + the three group kinds) in every system prompt | 07 Part 1/2 |
| Intro reads docs + trimmed code; code only when docs are absent | 06, 07 §2.1 |
| Block text reads docs + full code, explains only its range | 06, 07 §2.4 |
| Block plan: CoT justifies the count → `block_count` field → per-block `description` | 04, 07 §2.3, 08 |
| `NodeContext` actually filled (docs, children, parent, caller) — today it's empty strings | 06 |
| Prompts as `ChatPromptTemplate` constants; strings at the `structured_call` boundary | 07 Part 1 |
| `max_tokens` raised to runaway-guard sizes; cap hit = failed attempt | backend/02, 05 |
| `PROMPT_VERSION = "2"`, `SCHEMA_VERSION = "2"` | 04, 07 |

## Reality check (measured 2026-07-11 — re-verify, don't trust)

- `src/backend/app/walkthrough/context.py` — `build_context` hardcodes
  `docs_excerpt=""`, `parent_line=""`, `child_lines=[]`, `caller_line=None`. The
  whole 06 context design is unimplemented.
- `src/backend/app/walkthrough/prompts.py` — plain string builders, no rules, no
  glossary, no output layer. A skeleton of 07.
- `src/backend/app/walkthrough/graph.py` — `GraphNode` has no `documents` and no
  parent pointer. Domain nodes carry `documents: Set[str]` (id refs like
  `DocumentSchema/...`); `repos.document_repo.get_by_id(doc_id)` resolves one
  (`DocumentRepo` exists in `app/core/repository/__init__.py`, field `document_repo`).
- `src/backend/app/agent/llm/fake.py` — `FakeLLM` constructs `BlockPlan(...)`
  directly. It breaks the moment Step A lands, so Steps A and F happen in one pass.
- `src/backend/app/agent/llm/structured.py` — `CALL_PARAMS` has
  `"block_plan": {"temperature": 0.2, "max_tokens": 400}`.
- `src/backend/app/walkthrough/service.py` — `_stream_run` has `graph` in scope
  (line with `graph = await load_traversal_graph(...)`) but `run_pipeline` never
  receives it. That's the seam for context prefetch.

---

## Step A — schemas: BlockPlan v2 + version bumps

File: `src/backend/app/walkthrough/schemas.py`

Find `class PlannedBlock(BaseModel):`. Replace `PlannedBlock` and `BlockPlan` with —
**field order matters, it is the CoT contract (08)**, and the `Field(description=...)`
strings are sent to the model with the JSON schema, so copy them exactly:

```python
class PlannedBlock(BaseModel):
    start_line: int
    end_line: int
    focus: str = Field(
        max_length=100,
        description=(
            "User-facing label of what this block DOES, e.g. "
            "'validate the card fields'. At most 100 characters."
        ),
    )
    description: str = Field(
        description=(
            "One complete sentence to the narrator who will explain this block: "
            "what it does and why the code needs it."
        ),
    )


class BlockPlan(BaseModel):
    reasoning: str = Field(
        description=(
            "Think in order: (a) the code's overall structure, (b) where the "
            "natural seams are, (c) how many blocks that gives and why."
        ),
    )
    block_count: int = Field(
        description=(
            "The number of blocks your reasoning justified. "
            "blocks must contain exactly this many entries."
        ),
    )
    blocks: list[PlannedBlock]
```

Then find `class BlockStep(BaseModel):` and add one field after `focus`:

```python
    description: str = ""
```

(Persisted for evals and previous-block context. The frontend zod schema in
`src/frontend/.../walkthrough/types.ts` does **not** need this field — zod ignores
unknown keys on the patched mirror. Do not touch the frontend.)

Then find `SCHEMA_VERSION = "1"` / `PROMPT_VERSION = "1"` and bump both to `"2"`.

## Step B — validator: the commitment check

File: `src/backend/app/walkthrough/validators.py`

In `validate_block_plan`, right after `errors: list[str] = []`, add the count check
**before** the early `return` for missing lines (a wrong count is wrong regardless):

```python
    if plan.block_count != len(plan.blocks):
        errors.append(
            f"block_count says {plan.block_count} "
            f"but you returned {len(plan.blocks)} blocks",
        )
```

## Step C — graph: documents, parents, group provenance

File: `src/backend/app/walkthrough/graph.py`

1. `GraphNode` gains two fields (defaults keep every existing constructor call valid):

```python
    documents: list[str] = field(default_factory=list)   # DocumentSchema id refs
    parent_id: str | None = None
```

2. In `graph_node_from_domain`, populate `documents` from the domain node:
   `sorted(str(d) for d in (getattr(node, "documents", None) or set()) if d)`.
   Cap at 3 (06: first ones win).

3. In `build_graph`, after the `by_id` dict is filled, add a second pass setting
   `parent_id`: for each node, for each `child_id` in `node.children`, if the child
   exists and its `parent_id` is still `None`, set it to the node's id.

4. Add a provenance-aware sibling of `expand_children` (do not change
   `expand_children` itself — traversal uses it):

```python
def expand_children_with_groups(
    graph: dict[str, GraphNode],
    node_id: str,
    group_name: str | None = None,
) -> list[tuple[str, str | None]]:
    """Like expand_children, but remembers which group a child came through."""
    node = graph.get(node_id)
    if not node:
        return []
    ordered: list[tuple[str, str | None]] = []
    for child_id in node.children:
        child = graph.get(child_id)
        if child and child.kind == "group":
            ordered.extend(
                expand_children_with_groups(graph, child_id, child.name),
            )
        else:
            ordered.append((child_id, group_name))
    return ordered
```

## Step D — context: fill NodeContext for real

File: `src/backend/app/walkthrough/context.py`

The split (06): **graph-derived** context (docs, children, parent, caller, tour) is
prefetched by the service before the pipeline runs; **code-derived** context
(`numbered_code`, `intro_code`) is added by the pipeline, which already loads code.

1. Extend the `NodeContext` dataclass with the fields 06 lists — new ones are
   `intro_code: str | None = None`, `block_description: str | None = None`, and
   rename `previous_focus_lines` → `previous_block_lines` (update `prompts.py` and
   `pipeline.py` references in Steps E/F — grep for `previous_focus_lines` after, it
   must have zero hits).

2. Add the async prefetch builder. Shape (fill in per the 06 Formats section —
   exact caps and strings live there):

```python
async def build_contexts(
    graph: dict[str, GraphNode],
    visit_list: VisitList,
    repos: Repositories,
) -> dict[int, NodeContext]:
    """One NodeContext per stop, keyed by visit order. No code fields yet."""
```

   Per visit node:
   - `header` / `min_blocks` / `max_blocks` / `tour_position` / `first_seen_ref`:
     keep the existing `build_context` logic (reuse it, don't duplicate).
   - `docs_excerpt`: for each of the node's ≤ 3 `documents` ids,
     `await repos.document_repo.get_by_id(doc_id)`; skip `None`s; render
     `### doc: {name}\n{data}` with a per-doc cap of 800 chars and a total cap of
     ~2400 chars, appending `[…]` where cut. Empty result → `""` (the prompt layer
     omits the section — 07).
   - `child_lines`: `expand_children_with_groups(graph, visit.node_id)`, sorted with
     `sort_children_by_source` semantics, rendered
     `· {name} ({kind}) — {description}` or, when the group name is not `None`,
     `· {name} ({kind}, grouped under "{group}") — {description}`; cap 20 then
     `…and {n} more`. Skip children with no description rather than printing ` — `.
   - `parent_line`: from `graph[visit.node_id].parent_id` →
     `in {kind} {name} — {description}`; `""` when no parent.
   - `caller_line` (contextual stops only): `visit.parent_order` indexes
     `visit_list.nodes` — render the caller the same one-liner way.
   - For call stops, docs/children come from the **target** node
     (`visit.target_id`) when it exists in the graph — the stop shows the target's
     code, so its context must match.

3. Add the intro trim helper (06 Formats, "Intro code trim"):

```python
def trim_for_intro(numbered_code: str, end_line: int) -> str:
    """Full code when <= 80 lines; else first 60 numbered lines +
    '[… trimmed: N more lines, through line {end_line}]'."""
```

## Step E — prompts: rewrite against 07 Part 2

File: `src/backend/app/walkthrough/prompts.py` — full rewrite.

Rules for this step:

- **Copy every prompt text from 07 Part 2 verbatim.** Do not improve wording in code;
  wording changes happen in 07 first (it is canonical), then here.
- `PERSONA` and `GLOSSARY` are module constants. **Every** system prompt starts
  `{persona}\n\n{glossary}` — including block plan and block text.
- System prompts are `ChatPromptTemplate.from_messages([("system", ...)])` constants
  with `.partial(persona=PERSONA, glossary=GLOSSARY)`. Their remaining input
  variables are only the numeric/typed slots (`node_type`, `min_blocks`,
  `max_blocks`, `start_line`, `end_line`, `block_start`, `block_end`).
- User messages have **data-dependent sections** (omit-when-empty — 07 Part 1), so
  they are assembled by a tiny helper, not a fixed template:

```python
def _sections(*pairs: tuple[str, str | None]) -> str:
    """('documentation (may be truncated)', ctx.docs_excerpt), ... — skips empties."""
    parts = [f"### {title}\n{body}" for title, body in pairs if body]
    return "\n\n".join(parts)
```

- Each public function returns the two strings `(system, user)` — the
  `structured_call` boundary stays strings, `FakeLLM` and transport untouched.
- Section order and the final task line ("Introduce this node now." /
  "Split into {min}-{max} blocks now." / "Explain your block now.") exactly as 07
  shows them.
- Intro user prompt: `### code (may be trimmed)` uses `ctx.intro_code`, never
  `ctx.numbered_code`. Block plan and block text use `ctx.numbered_code` (full).
- Block text user prompt: the `### your block` section carries both lines —
  `Lines {a}-{b}: {focus}` and `Planner's note: {description}` — and
  `### previous blocks covered` renders `ctx.previous_block_lines` one per line.
- The block-plan retry suffix (`Your previous answer failed validation: ...`) is
  already appended by `structured_call`; do not add it here too.

## Step F — pipeline + fake provider wiring

File: `src/backend/app/walkthrough/pipeline.py`

- `run_pipeline` gains a `contexts: dict[int, NodeContext]` parameter; drop the
  internal `build_context` calls; per visit use `ctx = contexts[visit.order]`, then
  set `ctx.numbered_code` and `ctx.intro_code = trim_for_intro(...)` after
  `_load_numbered_code`.
- Block-text context: copy the stop context (`dataclasses.replace`) and set
  `block_focus`, `block_description=block.description`, `block_start`, `block_end`,
  `previous_block_lines`. Previous lines format (06):
  `f"lines {b.start_line}-{b.end_line}: {b.focus} — {b.description}"`.
- `BlockStep(...)` construction now passes `description=block.description`
  (fallback plans set it to `""` — Step F's `fallbacks.py` change below).
- `fallbacks.py`: `even_split_plan` and `single_block_plan` must set
  `block_count=len(blocks)` and `description=""` per block, or every fallback now
  crashes schema validation.

File: `src/backend/app/walkthrough/service.py`

- In `_stream_run` (and nowhere else), after `visit_list = build_visit_list(...)`:
  `contexts = await build_contexts(graph, visit_list, repos)`, passed to
  `run_pipeline`.

File: `src/backend/app/agent/llm/fake.py`

- The `block_plan` branch builds `BlockPlan(reasoning=..., blocks=blocks)` — it must
  now pass `block_count=len(blocks)` and give each `PlannedBlock` a
  `description=f"Covers {focus}."`-style complete sentence. Same pass as Step A.

File: `src/backend/app/agent/llm/structured.py`

- `CALL_PARAMS` → intro `max_tokens=700`, block_plan `1200`, block_text `800`, with
  the runaway-guard comment from backend/02 (caps are ~3× the largest honest
  completion; **never** length control — length is the prompt's job).
- Leave a `TODO(finish_reason)` where the real provider call will land: a response
  with `finish_reason == "length"` must count as a failed attempt even if it parses
  (backend/02) — user-facing text is complete sentences and paragraphs, never a cut.
  `FakeLLM` has no finish_reason; nothing to do there yet.

## Step G — tests

Dir: `src/backend/tests/unit/walkthrough/`

- `test_validators.py`: add a case — plan with `block_count=3` but 2 blocks →
  exactly one error mentioning both numbers.
- New `test_context.py`: docs excerpt renders `### doc:` headers, respects caps, is
  `""` for a node without docs; child line through a group carries
  `grouped under "..."`; a >80-line node's `intro_code` ends with the
  `[… trimmed:` marker naming the real end line; contextual stop gets a
  `caller_line`.
- New `test_prompts.py`: every system prompt contains `code-element group` (the
  glossary snapshot check from 07); intro user prompt with `docs_excerpt=""` does
  **not** contain `### documentation`; with docs it contains both `### documentation`
  and `### code`; block-plan system prompt quotes the same `{min_blocks}`/`{max_blocks}`
  numbers the validator enforces.
- Update `test_pipeline_blocks.py` / `test_pipeline.py` fixtures for the new
  `block_count`/`description` fields.

## Prove it

```bash
cd src/backend && uv run pytest tests/unit/walkthrough -q
```

All green (modulo any failures the README already lists as pre-existing — check
there first, and do not "fix" those here; they belong to fix 04).

Then the end-to-end eyeball with the fake provider (WALKTHROUGH_LLM_PROVIDER=fake):

```bash
cd src/backend && uv run python -m app.walkthrough.cli <project_id> <node_id> 1
```

- `hello` frame session has `"schema_version": "2"` and `"prompt_version": "2"`.
- Block frames carry non-empty `focus` **and** `description`.
- Nothing in any frame contains a half JSON or a text ending mid-sentence.

Anything suspicious that this doc did not tell you to change → README parking lot.
