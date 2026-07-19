# v2 · 07 — Subtask interactions & node selection (the call rule)

[03](03-detail-panel.md) specs how subtasks *look*; this doc specs how they
are **added, linked, and unlinked**, and how **nodes are selected** for
anchoring anywhere in the feature — including the rule that **calls are
never anchored: selecting a call resolves to its target function or
class**.

## A · Subtasks

### `+ Add subtask` — one input, two outcomes

Clicking the dashed button turns it into an inline row at the bottom of
the subtask list (same row metrics as the list, input styled like the
note input in 03 §8):

1. **Type-to-search first.** As the user types, a dropdown lists matching
   **existing open tasks** (title + `VN-n` key, from the board query cache
   — no fetch), excluding the task itself, its ancestors, and tasks
   already linked. Picking one calls `add_subtask(child_id)` — **this is
   the DAG entry point**: it's how *Refactor dd()* ends up under both the
   epic and the bug, and the child's `⑂ shared` chip appears by itself.
2. **Enter with no pick = create-and-link.** The text becomes a new task
   via the inline-create payload: type `task`, default column, no
   priority, **no anchor** (deliberate — a plain subtask states intent;
   anchoring is a separate act, or comes from suggestions below).
3. `Esc` cancels; empty input never submits.

Cycle refusals surface the server sentence verbatim as a toast
(`"VN-11 already contains VN-9 through the subtask graph — adding this
edge would create a cycle."`) — the input stays open with its text so the
user can pick differently.

### `✦ Suggest from dependencies`

Opens the checkbox list (same rows as the New-task modal's suggestions:
`checkbox · kind icon · qname` mono) seeded from the task's **first
resolved anchor** via the suggest endpoint. Each checked row
creates-and-links a subtask titled after the dependency and **anchored to
that dependency** — the suggestions are already call-resolved (the
endpoint reads `call_children → target_function/target_class`), so this
surface obeys the call rule by construction. Zero suggestions → the
button shows a quiet `no dependencies found` inline note instead of an
empty dialog.

### Unlink (addition beyond the mock — required for a DAG)

Row hover reveals a trailing `✕` (matches the header ✕ treatment, 12px):
calls `remove_subtask(parent, child)` — **edge removal only**, the child
task always survives. On a shared child this just removes one parent; the
`⑂ shared` chip disappears when one parent remains. Without this
affordance a mislink is permanent, which is worse than deviating from the
mock.

### Ordering & numbers

- The schema stores subtasks as a **set** ([06](06-subtasks-as-self-references.md)),
  so render order must be imposed: open children first (by column order),
  done children last, `VN-n` key ascending within groups — deterministic
  across reloads.
- The `SUBTASKS · n/n` heading and card `✓ n/n` use the API's
  closure-deduped `subtask_progress` (the mock computes direct children;
  at depth 1 they agree, and the closure number stays truthful for nested
  DAGs).

## B · Node selection — every anchor flow, one picker, one law

### Where nodes get selected

| Surface | Flow |
|---|---|
| New-task modal | pre-filled chip (context/scope) + `+ add` opens the picker |
| Detail panel `+ Add anchor` | picker → idempotent `add_anchor` |
| Re-anchor | candidate picker (existing flow), seeded by snapshot qname |
| Canvas/tree context `New task here` | node preset → modal chip |
| `⚓ Anchor current node` chip | tab's active node, one click |

### The picker

Reuse the `SelectNodeDialog` machinery
(`Dashboard/components/SelectNodeDialog.tsx`): search input filtering by
qname/name, rows = kind icon in its 01 color + qname **mono 12px**, kind
label right-aligned mono 9.5px `#5c6270`. Anchorable kinds:
**function · class · file · folder**. **Calls are not listed.** Groups and
virtual/group nodes are not listed either — anchors bind to code, not to
presentation groupings.

### The call rule (settled)

**A call can never be an anchor. Any call entering an anchor flow
resolves to its target — `target_function` or `target_class` — and the
anchor binds to that.**

- Right-click a call node → *New task here* → the modal chip already shows
  the **target** (`ƒ main.dd`, not `↦ dd()`); the client resolves via
  `CallNode.target` (`types/project.ts:68`).
- `⚓ Anchor current node` while a call is active → chip names the target.
- **Server is authoritative**: `_snapshot_anchor` on a `CallSchema/…` id
  resolves `target_function ?? target_class` and snapshots *that* node.
  Client pre-resolution is a courtesy; the service enforces the law, so no
  path (agent tools included, later) can create a call anchor. Drop
  `"call"` from the anchorable kind map; `KIND_ICON.call` stays for
  display-only contexts.
- **Dangling target** (the known parser failure mode —
  `CallSchema.target_function` dangling after renames): refuse with a
  sentence, house-style 422: `"This call's target no longer exists on this
  branch — anchor the function or class directly."`
- **Idempotency interplay** (decision 9 unchanged): two different call
  sites of the same function resolve to the same target → the second add
  is a no-op, not a duplicate.

**Why:** calls are occurrences of a relationship, not stable subjects —
the parser deletes and recreates them on every reparse, making them the
most volatile node kind; a task "about a call" is really about the callee.
Resolving also concentrates the hot-node signal **on the function**
instead of scattering open-task counts across call sites — the convergence
feature gets stronger, not weaker.

### Kind snapshot after resolution

The stored anchor snapshot records the **target's** qname/kind
(`kind: function|class`), so unresolved-state display, re-anchor
candidates, and hot counts all speak about the real subject; nothing
downstream ever sees `kind: "call"`.

## Test gate

- Add-subtask search links an existing task; the shared chip appears on
  the second parent; unlink from one parent removes the chip, the child
  survives.
- Inline Enter creates a new task in the default column, linked, no
  anchor; cycle attempt shows the server sentence and keeps the input.
- *New task here* on a call node pre-fills the target function chip;
  creating anchors the function (raw document check).
- `add_anchor` with a `CallSchema/` id anchors the target; with a dangling
  call → 422 with the sentence; two call sites of one function → one
  anchor.
