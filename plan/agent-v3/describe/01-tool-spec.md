# Describe 01 — Tool Spec

The context farmer. One structured call per node, children first, each writing a
2–3 sentence description onto the node. It looks like the least glamorous tool
in the system and matters more than any of them: every child line, sibling line,
parent line, and NodeCard in every future prompt is built from what this tool
writes.

## The spec

```python
class DescribeArgs(BaseModel):
    node_id: str = Field(description="The attached node to describe from. Its "
                                     "children are described too, down to depth.")
    depth: int = Field(1, ge=0, le=5, description="Levels below the node to include. "
                                     "0 = just this node. The user confirms this.")
    overwrite: bool = Field(False, description="Replace existing agent-written "
                                     "descriptions. Never touches human-written text.")

SPEC = ToolSpec(
    name="describe_nodes",
    description="Write short descriptions for a node and its children (children "
                "first, so parents are summarized from fresh child summaries). "
                "Improves every later walkthrough, doc, and answer. Costs one "
                "LLM call per node — an estimate is shown for approval.",
    input_model=DescribeArgs,
    kind="task",
    confirmation="over_threshold",       # "always" when overwrite=True (shared/03)
    render="run_checklist",
    handler=DescribeTool(),
)
```

No `user_query` arg — deliberate; the README's flagged divergence. Descriptions
are canonical shared context, read blindly by every future prompt; an
intent-angled description misleads the next question. The agent uses the user's
intent to choose the *node and depth*, never the content.

## `estimate()`

```
1. subtree_max = subtree_max_depth(repos, node_id)         (v2 WOQL probe, reused)
2. plan = walk(order="post", depth=clamp(depth))           (shared/01)
3. writable = [n for n in plan if would_write(n, overwrite)]   # deterministic
4. return ToolEstimate(
       items=len(writable), llm_calls=len(writable),       # EXACT — one call per node
       label=f"{len(writable)} nodes · {len(writable)} LLM calls"
             + (f" · {skips} already described" if skips else ""),
       over_cap=len(writable) > DESCRIBE_ITEM_CAP,
       knobs={"depth": {"value": depth, "max": subtree_max},
              "overwrite": overwrite})
```

The confirm card shows the skip count — "32 nodes · 20 calls · 12 already
described" tells the user the tool respects existing work *before* they approve.

## `run()` — the loop

```
pin branch + commit → plan (post-order) → open ToolRun artifact (all items pending)
for item in plan:
    if has_description and not (overwrite and agent_origin):  → skipped_existing
    ctx    = factory.build(item.node_id, preset="describe_node")   (describe/02)
    result = structured_call("describe", DescribeOut, system, ctx)  # try → retry-with-errors
    if result is None:                                       → failed (leave blank — describe/02)
    else: write description + meta; record commit            → written, preview=first sentence
    persist run item; patch artifact; tick progress
summary → {"run_id", "written", "skipped", "failed", "status"}
```

The **fresh-summary handoff** is the whole point of post-order and lives here:
each completed item's new description goes into an in-run map
`{node_id: description}`; when a parent's context is built, the factory is given
this map as an **override layer** — parents read this run's fresh text, not the
possibly-stale stored text. (One dict argument on the preset build; no factory
redesign.)

## What the agent does around it

- Suggests it when enrichment blocks or NodeCards show empty descriptions
  (`…` content in the serializer is the cue — v2 made that honest hole visible
  precisely for this).
- Orders it before document/walkthrough runs on the same subtree (the quality
  gradient, README).
- After the run: one line from the summary — never re-narrates the checklist.

## Evals (the cheapest in the system)

- validator first-pass rate (how often attempt 1 survives validation);
- % nodes described after one run over a fixture project;
- regression fixture: re-run on prompt-version bump, diff the previews.
