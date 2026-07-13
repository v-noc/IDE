# Describe 02 — Prompt, Context, and the First-Sentence Contract

What one describe call sees, what it must produce, and the two rules that keep
the output from poisoning the system: the first-sentence contract and the
leave-blank fallback.

## The output shape

```python
class DescribeOut(BaseModel):
    reasoning: str      # 1 sentence, private — the model's read of the node (CoT-first, MVP 08 rule)
    description: str    # 2–3 sentences; the FIRST sentence must stand alone
```

## The first-sentence contract (how 2–3 sentences coexist with one-line lists)

v3 upgrades descriptions from the MVP's one-liners to 2–3 sentences — but the
entire v2 context system (child lines, sibling lines, NodeCards, project header)
is budgeted around **one line per node**, with caps enforced by construction.
Two obvious fixes were rejected:

- *store two fields (`summary` + `description`)* — a node-schema migration, two
  things to validate, two things to drift apart;
- *let lists truncate at N chars* — mid-sentence cuts read broken and the
  serializer would be doing runtime trimming, which v2's principles forbid.

**Decision: one field, structural rule.** The prompt requires — and the
validator enforces — that **sentence 1 works alone as a one-line summary**
(what it is + what it's for, ≤ 120 chars). Sentences 2–3 add the how/why detail.
Consumers pick deterministically:

| Consumer | Uses |
|---|---|
| `<children>` / `<siblings>` one-liners, NodeCards, project header | sentence 1 only (serializer splits at the first sentence boundary — deterministic, no LLM) |
| `<description>` blocks (attached-node enrichment, intro contexts), node inspector UI | the full 2–3 sentences |

Caps stay intact by construction, the graph schema doesn't change, and the
richer text is there whenever a consumer has room for it.

## The context (factory preset `describe_node` — one screen, one job)

| Node kind | Context |
|---|---|
| function / class with code | own numbered code (intro-trim rules: ≤ 80 lines full, else head + honest marker) · fresh child summaries (calls → their targets' one-liners) · parent **name + kind only** |
| folder / file (containers) | fresh child summaries (this run's, via the override map — describe/01) · own docstring/module header if code carries one · parent name + kind only |

Explicitly **not** included, with why:

| Excluded | Why |
|---|---|
| parent's description | it doesn't exist yet — post-order writes it after this node; including stale parent text would anchor the child on the old tree |
| siblings | a description says what the node *is*, not what it isn't; siblings help disambiguation in Q&A (v2 enrichment), not authorship — and they'd double the context for no measured gain |
| attached docs | docs describe intent at a higher level; a *description* must be grounded in what the code actually does. Docs feed the document tool instead |
| `<user_intent>` | canonical-context poisoning (README divergence) |

## The prompt (registry: `describe.node`, own version)

```
Write a description of this {node_type} for developers who will see it in
lists and tooltips before they ever open the code.

Rules:
1. 2–3 sentences. Sentence 1 must stand alone: what this {node_type} is and
   what it is for, under 120 characters — it will be shown by itself in lists.
2. Sentences 2–3: the essential how or why — key behavior, important
   collaborators (by name), or the reason it exists. No restating sentence 1.
3. Ground every claim in the provided code and child summaries. Never invent
   names, parameters, or behavior. If the code is trivial, two sentences are
   enough — never pad.
4. Banned: starting with "This function/class/file…" (the reader sees the kind
   already) · line numbers · file paths · meta-talk ("the context", "the code
   shows") · marketing adjectives.
```

Validation (code, before accepting):

- 2–3 sentences; sentence 1 ≤ 120 chars; total ≤ 400 chars;
- banned-opener regex; no line numbers / paths;
- every capitalized identifier and `code_name` mentioned must appear in the
  provided context (the cheap anti-invention grep, from the MVP's doc
  validator).

## The fallback: leave blank, never write junk

This is the one place v2's degrade-never-abort policy deliberately bends. The
walkthrough can fall back to a stored description because its output is a
*display artifact*; a fallback **description** would become *input to every
future prompt* — fabricated context, laundered as data, compounding with each
tour and doc built on it.

So: retry once with the validator messages appended (the `structured_call`
pattern); on second failure the node **stays undescribed**, the item is
`failed` with the validator message as `error`, and the summary reports it. An
honest hole (`…` in the serializer, visible cue in every card) beats confident
filler — the same reasoning, one level deeper, as keeping docs out of the MVP's
block planner.
