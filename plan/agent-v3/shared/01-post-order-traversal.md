# Shared 01 — The Post-Order Plan

Both v3 tools plan their work the same way: walk the subtree under the selected
node, children before parents, to a user-confirmed depth. The plan is code
(never the model's decision), and it reuses the walkthrough's traversal machinery
rather than growing a second tree-walker.

## Decision: one walker, two orders

`app/walkthrough/traversal.py` already knows how to load the subtree, flatten
groups, and respect depth. It gains one parameter instead of a sibling module:

```python
walk(graph, start_node_id, depth, order: Literal["pre", "post"]) -> list[PlanNode]
```

- `pre` — the walkthrough's existing order (reader's order, outside-in).
  Behavior unchanged; existing tests must pass untouched.
- `post` — children emitted before their parent (author's order, inside-out).
  Same visit set, reversed dependency direction.

**Why one function.** The subtle rules — group transparency, call handling, depth
counting — must never fork. A bug fixed in one order is fixed in both; the MVP
already paid for these rules once.

## What's in the plan (and what's skipped)

| Node kind | In the plan? | Why |
|---|---|---|
| folder / file / class / function | yes | all can carry descriptions and docs |
| call nodes | **no** | the call's *target* gets described/documented at its own position; describing a call site would duplicate the target's text everywhere it's called |
| groups (all three kinds) | flattened, never planned | groups are visual boxes, not code (the MVP glossary rule); their members join the parent's children |
| nodes with existing text | planned, then **skipped at execution** (`skipped_existing`) unless `overwrite` | the skip must be visible in the checklist — silent skipping hides why a node still has stale text |

**Why skips happen at execution, not planning.** The estimate stays honest
either way (skip counting is deterministic — the plan is code), but a skipped
node *appearing in the checklist* tells the user "this one already had text" —
information they need to decide whether to re-run with overwrite.

## Depth, exactly as the walkthrough defines it

- `depth` = levels below the selected node included in the plan (0 = the node
  alone). Same knob, same confirm-card slider, same WOQL `subtree_max_depth`
  probe capping the slider (v2 harness/03), same `HARD_MAX = 5`.
- **The boundary rule:** a planned parent at the depth edge summarizes from
  whatever its children have — fresh summaries when the children were in the
  plan, *existing* descriptions when they weren't, and honest name-only entries
  when nothing exists. The context builder marks the difference; the prompt
  never pretends stale is fresh (describe/02).

## Caps (the cost guards, per tool)

| Constant | Value (start; tune by dogfooding) | Why it differs |
|---|---|---|
| `DESCRIBE_ITEM_CAP` | 150 | one small call per node; deep coverage is the point of the tool |
| `DOCUMENT_ITEM_CAP` | 30 | docs are the largest outputs in the system; 30 docs is already a book |

Over the cap → `estimate.over_cap` → the harness refuses with the shrink hint
("depth 3 is 210 nodes — try depth 2"), exactly like the walkthrough's visit cap.

## Estimates are exact here (nicer than the walkthrough's)

Both tools make **one structured call per planned item**, so
`llm_calls = len(plan_after_skip_filter)` — not an approximation. The estimate
label says so plainly: "32 nodes · 32 LLM calls" (describe), "9 docs · 9 larger
calls" (document). The walkthrough's `~` hedge isn't needed; don't inherit it.

## Cancellation and partial runs

Checked between items, as always. Because the order is post-order, a cancelled
run has a useful property worth stating in the UI: **everything written so far is
complete and self-consistent** — children are never left waiting for a parent
that describes them, because parents come last. A cancelled describe run at 20/32
items means 20 finished descriptions, not 20 halves.
