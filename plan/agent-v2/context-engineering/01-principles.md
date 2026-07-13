# Context Engineering 01 — Principles

The rules every context block in the system obeys, regardless of who consumes it
(the chat agent or a tool's micro-call). The MVP proved these on the walkthrough;
v2 promotes them to system-wide law.

## Principle 1 — context is assembled, not searched

The graph already knows a node's parent, siblings, children, docs, and code. We
*assemble* a neighborhood deterministically from the graph, instead of letting the
model fish for it with tool calls.

**Why.** Deterministic assembly is instant, free, and testable; tool-call fishing
is slow, token-expensive, and different every run. It also fits this build's
scope: with search/query tools skipped, assembly isn't just cheaper — it's the
only mechanism. A model that starts the turn already oriented answers simple
questions with **zero** tool calls, which is also our cheapest quality metric
(percentage of attached-node questions answered without any tool call).

## Principle 2 — caps by construction, never runtime trimming

Every list in a context block has a cap (10 siblings, 20 children, ~600 doc
tokens, 80 code lines before intro-trim). The caps live **inside the builder**
(02), so every consumer inherits them and none re-implements trimming.

**Why.** "Trim if too long" written at call sites drifts: one consumer forgets,
one trims differently, budgets regress silently. A cap inside the single builder
is enforced everywhere by construction, and the builder unit-tests its own
worst-case budget — regressions fail in CI, not in the bill.

## Principle 3 — XML-ish tags, one serializer

All graph context renders as nested tags:

```xml
<attached_node id="n42" kind="function" name="charge" path="payments/service.py" lines="10-62">
  <description>Charges a card and returns a receipt.</description>
  <parent kind="class" name="PaymentService">Orchestrates charge and refund flows.</parent>
  <siblings>
    <node kind="function" name="refund">Reverses a completed charge.</node>
  </siblings>
  <children>
    <node kind="call" name="validate_card()">Checks number, expiry and cvv format.</node>
  </children>
  <doc title="Payment flow">Charging happens in two phases: tokenize, then capture. […]</doc>
  <code lines="10-62">
  10 | def charge(self, card: Card, amount: int) -> Receipt:
  ...
  </code>
</attached_node>
```

**Why tags and not prose or JSON.**

- **Nesting mirrors the graph 1:1.** Folder → file → class → function is
  containment; nested tags *are* containment. Prose bullet lists lose "which
  belongs to which" at depth 2+; JSON wastes tokens on quoting and braces and
  reads worse for models.
- **Explicit boundaries stop bleed.** A closing tag ends a section unambiguously;
  models respect tag fences far better than blank lines. Docs stop leaking into
  code; siblings stop being mistaken for children.
- **Attributes vs content = identity vs meaning.** Machine-checkable identity
  (`name`, `kind`, `lines`) rides as attributes; human meaning (descriptions,
  docs) is content. Same discipline as the MVP's `focus` vs `description`.
- **Greppable in traces.** "Did the intro prompt include siblings?" is a one-line
  grep against recorded prompts — context evals become greps.

**The honest caveat, stated as a rule:** this markup is **model-facing, never
parsed back**. Well-formedness is a non-goal; *consistency* is the contract —
which is why exactly one module (`app/agent/context/xml.py`) renders it.

## Principle 4 — rendering rules

- **Allowed attributes**: `id`, `kind`, `name`, `path`, `lines`, `title` — nothing
  else. Everything with meaning is content.
- **One-liner form**: a node whose job is orientation renders on one line —
  `<node kind="function" name="charge">charges a card…</node>`. Undescribed nodes
  render `…` as content, honestly (an honest hole beats confident filler — and it
  is the future cue for a describe tool).
- **Code is raw.** Inside `<code>`, the numbered-line format from the walkthrough
  is kept verbatim (real absolute line numbers — validation and Monaco
  highlighting depend on them). No escaping, no CDATA; nothing parses it back, so
  `<` in code is harmless.
- **Empty = omitted.** No empty tags, ever. A missing `<doc>` *means* "no docs";
  an empty one invites the model to invent content for it.

## Principle 5 — what never enters the agent's context

| Excluded | Why |
|---|---|
| Whole-subtree dumps | context is the *neighborhood*, not the world; depth beyond the caps is a future query tool's job |
| Artifact payloads | the model gets compact tool summaries; artifacts render to the user (data-model/01) |
| Rewritten user messages | enrichment **adds** blocks, never edits the user's words — auditability, and distillation mistakes stay visible |
| Past turns' reasoning parts | never replayed across turns — cost without signal, and summary-channel CoT was never ours to replay (harness/04) |
| Mixed commits | enrichment reads at head; each artifact reads at its own pinned commit — never blended in one prompt |
