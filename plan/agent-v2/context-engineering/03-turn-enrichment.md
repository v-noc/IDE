# Context Engineering 03 — Turn Enrichment

What happens to a user message *before* the model sees it. Three deterministic
injections, zero LLM calls. This is the whole "the agent understands the selected
node" mechanism.

## 1 — Project header: always, every turn

`ProjectContextMiddleware` renders into the system prompt on **every** turn:

```xml
<project name="v-noc">
Interactive code-graph IDE: TerminusDB-backed node graph over a codebase,
rendered on a canvas with walkthroughs, descriptions and docs generated per node.
</project>
```

(the `project_header` preset — name and description come from the `ProjectNode`
the UoW already resolved for the request).

**Why always, and why in the system prompt.** The agent must never answer "what is
this project?" from thin air, and its status lines should name the project
naturally. Injecting per-turn instead of baking it into a static prompt means the
same agent code serves every project; putting it in the *system* prompt (dynamic
content in a static position) keeps it out of the user-message stream where it
would be re-sent and re-read as conversation.

The stable domain glossary (node kinds, groups, what a walkthrough is) sits next to
it — shared with the walkthrough's `GLOSSARY` constant in
`app/walkthrough/prompts.py`, moved to the prompt registry so both cite one source
(prompts/01).

## 2 — Attached nodes: the `<attached_node>` block

For each `NodeRefPart` in the incoming message, `NodeEnrichmentMiddleware` builds
the `attached_node` preset (context/02): description, **parent title +
description, sibling one-liners**, children one-liners, docs excerpt, and trimmed
code when exactly one attached node has code.

**Why parent + siblings, not just children.** A node explains best in its
neighborhood: the parent says what it belongs to; the siblings say what it is
*not* — with `refund` visible one line away, the model stops attributing refund
behavior to `charge`. Cheap, deterministic, and it reads like how a colleague
introduces code.

Budget rules (all inside the factory, inherited by construction):

| Rule | Value |
|---|---|
| Full block | only for ≤ 3 attached nodes; more → one-liner cards only |
| `<code>` | only when exactly **one** attached node has code; ≤ 80 lines full, else first 60 + a marker naming the real end line |
| siblings / children / docs | 10 / 20 / ~600 tokens |
| whole block | ~1.5k tokens typical, ~3k worst case by construction |
| past turns | fresh **once** — in later history the ref collapses to its one-line card (harness/01 history rules) |

**Why enrichment adds blocks and never rewrites.** The model must see what the
user actually said (auditability); and if our enrichment picks wrong, the error is
visible next to the original words instead of silently replacing them.

## 3 — Distilled intent: what flows into the walkthrough tool

The user says *"walk me through how retries end up calling charge twice — just a
quick overview"*, not "walkthrough n42 depth 1 verbosity=quick". The agent's job is
to translate, and the translation is **arguments, not prose**:

```python
walkthrough(
    node_id="n42",                 # from the NodeRefPart — the only legal source
    depth=1,                       # SUGGESTED from the wording; user confirms (harness/03)
    user_query="Understand how retries end up calling charge twice.",
    verbosity="quick",             # quick | normal | detailed
)
```

Distillation rules in the orchestrator prompt:

- `user_query`: **one sentence, the user's goal in their own plain words** — no
  ids, no tool talk; empty when the user expressed no particular angle.
- `verbosity`: from explicit wording only ("quick", "briefly", "in detail",
  "deep dive"); default `normal` when unstated.
- `depth`: 0–1 for overview asks, 2–3 for "everything/in detail" asks, else 1 —
  it is only a prefill; the confirm card is where it becomes real.

The tool injects the intent into the **intro and block-text prompts only**:

```xml
<user_intent>Understand how retries end up calling charge twice.</user_intent>
```

with one prompt rule alongside: *angle the explanation toward the intent where the
code is genuinely relevant; never skip or distort what the block actually does.*

**Why the block plan never sees the intent.** Seams live in code. An intent-shaped
split would produce block ranges that mirror the question instead of the
structure, and plans would stop being stable across runs. Narration bends;
structure doesn't. (Same reason `verbosity` only touches narration prompts —
harness/03.)

**Why this is safe to ship early.** `user_query` and `verbosity` are pure
prompt-side additions: traversal, estimates, and validation are untouched. Both
are stored on the session for evals.

## Deferred on purpose: intent-driven stop gating

Using the intent to *skip* stops ("only the retry path" → 6 stops instead of 20)
is not in this build. The seam already exists — a visit-list filter between
traversal and pipeline, and `VisitNode.mode` already expresses reduced stops — but
it needs a per-stop relevance judgment (a classifier call per stop), UI honesty
for skipped stops, and an eval story for wrong skips. **Trigger to build:**
dogfooding shows long tours where most stops are noise for the asked question.
