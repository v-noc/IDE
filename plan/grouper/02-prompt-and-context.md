# Grouper 02 — Prompt, Context, Proposal Schema, Validator

One structured call per kind-partition turns a child roster into a validated
proposal. This doc is the whole model-facing surface: what it reads, what it
must return, and the laws the validator enforces.

## Context: the roster (assembled, not searched)

Per partition, via the context factory (context-engineering/02 — a preset,
not a hand-built string):

```xml
<parent>
  payments/ (folder) — Handles the card payment lifecycle end to end.
</parent>

<children count="14" kind="file/folder">
  charge.py (file) — Builds and submits the charge request.
  refund.py (file) — Issues refunds against settled charges.
  retry.py (file) — Retries failed charges with backoff.
  webhooks/ (folder) — (no description)
  …
</children>
```

- One line per child: `name (kind) — first sentence of its description`, the
  same serializer line every other tool uses (the describe tool's
  first-sentence contract is exactly what makes this roster cheap and good).
- `(no description)` is stated, not hidden — the model must not invent what a
  bare name doesn't say, and the prompt tells it so.
- **No code, no docs, no call edges in v1.** Names + one-liners are the
  grouping signal; pulling code for 60 children would blow the context for
  marginal gain. If evals show name-only children group badly, the seam is
  one factory flag — noted, not built.

## The prompt (system, registry-versioned like all v2 prompts)

Job: "organize these children into named groups a developer would find
obvious in hindsight." Rules, in the order the model reads them:

1. **Think first, in `reasoning`**: enumerate 2–3 candidate grouping
   dimensions this roster supports (by pipeline stage, by feature, by
   layer…), say which one wins and why, *then* write the groups. This is the
   CoT step — deliberately inside the structured call, so the choice lands
   in a field, not in vapor. (On models with a native reasoning channel the
   thinking row shows it too — harness/04 — but the schema never depends on
   that.)
2. **If a `<category>` is provided, it wins.** The user's dimension is the
   lens; discovery is only for the empty case. Never override it, never
   blend it ("by lifecycle, but also kind of by module").
3. `dimension`: one plain sentence naming the chosen dimension — it becomes
   the user-visible, user-editable explanation ("Grouped by pipeline stage:
   building, submitting, and reconciling charges."). Write it for the card.
4. Group `name`s: 1–3 words, noun phrases, unique, no numbering, no
   "Miscellaneous"/"Other"/"Utils"-shaped buckets — if members don't fit,
   leave them ungrouped with a reason.
5. `description` per group: one sentence, what unites the members — it will
   be written onto the group node itself (05) and read by future prompts.
6. Every child id appears **exactly once**: in one group's `member_ids` or in
   `ungrouped` with a reason. Only ids from the roster; order within groups
   is meaningless.
7. Respect the knobs: between `{min_groups}` and `{max_groups}` groups, each
   with at least 2 members.

## Proposal schema (the structured output)

```python
class ProposedGroup(BaseModel):
    name: str
    description: str
    member_ids: list[str]

class GroupProposal(BaseModel):
    reasoning: str                 # private: candidate dimensions + choice
    dimension: str                 # the explanation, user-facing + editable
    groups: list[ProposedGroup]
    ungrouped: list[UngroupedItem] # {node_id, reason}
```

`structured_call` with the v2 try→retry-with-errors pattern: one retry,
validator messages appended verbatim ("group 'Utils' has 1 member; children
[x, y] appear twice"). Two failures → `error` outcome with the last
validator message; nothing was written, nothing to undo.

## Validator laws (code, not vibes — same validator judges user edits at gate 2)

| Law | Why |
|---|---|
| every roster id exactly once (group ∪ ungrouped) | a silently dropped child is corrupted structure |
| no id outside the roster | fabricated node ids are impossible by construction elsewhere; keep it that way |
| `min_groups ≤ len(groups) ≤ max_groups` | the knobs are a contract, not a hint |
| every group ≥ 2 members | a group of one adds a click and removes nothing |
| kind homogeneity per group (partition guarantees it for the model; edits could break it) | the three group kinds each hold one child kind — a mixed group can't be written at all |
| names unique, non-empty, ≤ 30 chars; banned-bucket list (`misc`, `other`, `utils`, `stuff`, …) case-insensitive | names are canvas labels; buckets are the failure mode grouping exists to prevent |
| `dimension` non-empty, ≤ 200 chars | the explanation is required output, not optional garnish |
| ungrouped reasons non-empty | "left out" without a why is indistinguishable from a bug |

The validator is a pure function over `(GroupProposal, roster, knobs)` —
unit-tested exhaustively, shared verbatim between the model path (G1) and the
edit path (G2/03). One implementation or the two gates drift.

## Evals (fixtures from day one, v2 style)

- validator first-pass rate per model (the retry should be rare, not routine);
- % of pool grouped (persistently high `ungrouped` = the dimension discovery
  is failing);
- dimension-edit rate at gate 2 (if users rewrite the explanation constantly,
  rule 3's phrasing needs work);
- fixture rosters: a clean 14-file module, a mixed-kind node, a
  descriptionless roster, a 60-child cap case.
