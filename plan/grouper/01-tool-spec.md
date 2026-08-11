# Grouper 01 — Tool Spec

`group_children`: a v2 `ToolSpec` like the others (`kind="task"`,
`confirmation="always"`), plus the one new spec field this plan introduces —
`review="always"` (03). Registered in `app/agent/tools/`, one spec + one
module, per the v2 registry law.

## Args

```python
class GroupChildrenArgs(BaseModel):
    node_id: str          # the attached parent — only ids the user attached
    min_children: int = 4   # ge=2  — grouping threshold (see below)
    min_groups: int = 2     # ge=2
    max_groups: int = 6     # le=12 — validator ceiling; mock UI caps at 12
    category: str = ""      # optional dimension lens, the user's words
    regroup: bool = False   # dissolve agent-origin groups first (05)
```

Field notes, in the arg descriptions the model reads:

- `min_children` — "don't group unless the parent has at least this many
  ungroupable-free children." It is a *threshold*, not a per-group size: with
  the default 4, a parent with 3 direct children is refused (below), one with
  5 gets grouped. The agent may suggest a different threshold from the user's
  wording; the user owns it at gate 1.
- `category` — "the dimension the user asked to group by, in their words
  ('by lifecycle', 'by feature area'). Empty if they named none — the model
  will discover one." Same contract as the walkthrough's `user_query`: verbatim
  or empty, never invented.
- cross-rule: `min_groups <= max_groups` (pydantic validator; the frontend
  steppers already enforce it locally — frontendv2/03).

## The eligible pool (what "children" means exactly)

Direct children of `node_id` that are **not already inside a group**:

- children sitting directly under the parent → eligible;
- children inside a *human-drawn* group → excluded, always (README decision 3);
- children inside an *agent-origin* group → excluded unless `regroup=true`,
  in which case those groups are marked for dissolution and their members
  join the pool (the dissolution happens at write time, 05 — the run itself
  stays read-only);
- existing group nodes themselves are never members of a proposed group
  (no nesting in v1).

Mixed kinds are legal in the pool and resolved by partitioning: the pool
splits by group-kind mapping (folders/files → `structure_group`, classes/
functions → `code_element_group`, calls → `call_group`) and each partition is
grouped independently against the same knobs (02). A partition below
`min_children` is reported as-is, not padded.

## Refusals (before any LLM call, at estimate time where possible)

| Condition | Refusal sentence (returned to the agent, relayed to the user) |
|---|---|
| eligible pool < `min_children` | "only N ungrouped children — grouping would add a layer without removing any scanning cost" |
| pool > `GROUP_CHILDREN_CAP` (≈ 60) | "N children exceeds the grouping cap — group a subfolder first, or raise the threshold" |
| parent fully grouped already, `regroup=false` | "children are already grouped — say 'regroup' to restructure the agent-made groups" |
| pool can't satisfy `min_groups` × 2 members | "N children can't form M groups of at least 2 — lower min groups" |

Refusals are `ToolOutcome`s with `status: "refused"` and the reason — the
turn continues, the agent answers with the sentence (failure is boring).

## Estimate (gate 1) — honesty note

The mock's `14 children · ~6 LLM calls` was fixture drama. The real shape is
**one structured call per kind-partition, plus one retry margin**:

```
llm_calls = partitions * 2        # 1 proposal + ≤1 validator retry each
items     = len(pool)
label     = "14 children · 2 groups proposed · ~2 LLM calls"   # 1 partition
```

Knobs payload mirrors the args so the ConfigForm prefills:
`{"min_children": 4, "min_groups": 2, "max_groups": 6, "category": "",
"undescribed": k}` — `undescribed` powers the same gate-1 hint as document's:
*"9 of 14 children have no descriptions — run describe first for better
groups"* (text only, no auto-chaining; the describe→everything quality
gradient, agent-v3 README).

## The run lifecycle (two gates)

```
pending
  → awaiting_confirmation      gate 1: estimate + knobs      (v2, unchanged)
  → running                    roster → proposal → validate (→ retry once)
  → awaiting_review            gate 2: proposal on the card   (NEW — 03)
       user approves (with edits) ──→ running (write batch) → completed
       user cancels             ──→ cancelled (nothing written)
  → error                       validator failed twice / write failed
```

Two `running` stretches, both honest: the first spends LLM calls, the second
writes. Progress on the tool part: `{done, total, label}` with code-authored
labels — "proposing groups (1/2)", "writing groups (3/4)". The proposal
itself streams as an artifact doc (`group_proposal/<id>`, 03) so gate 2 has
its data the moment the state flips.

## Result (returned to the agent on completion)

```python
{"run_id": …, "dimension": "pipeline stage",
 "groups": [{"name": "Charge flow", "count": 6}, …],
 "ungrouped": 2, "edited_by_user": true, "status": "complete"}
```

The agent's closing line writes itself — "created 3 groups by pipeline stage;
2 children left ungrouped (you edited the proposal before approving)" — and
never re-narrates the member lists (the card holds those).

## Caps and constants

```python
GROUP_CHILDREN_CAP = 60    # pool size; refuse beyond
GROUP_MIN_MEMBERS  = 2     # validator law, not a knob
GROUP_MAX_KNOB     = 12    # max_groups ceiling (mock UI agrees)
```

One place, `app/agent/tools/group_tool.py` top, like the walkthrough's
`HARD_MAX_DEPTH`.
