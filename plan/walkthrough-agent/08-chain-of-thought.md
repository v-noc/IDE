# 08 — Chain of Thought

What CoT actually is, which variants exist, what works on small models, and exactly
where this project uses it. This is a learning doc as much as a design doc.

## What CoT is (and why it works)

A language model generates one token at a time, and each token can only be computed
from what is already in the window. "Chain of thought" means: **make the model write
its intermediate thinking before its answer**, so the answer is conditioned on that
thinking instead of being guessed directly.

The mechanical consequence people miss: **order is everything**. If the schema says
`{answer, reasoning}`, the reasoning is written *after* the answer — it becomes a
post-hoc justification and helps nothing. `{reasoning, answer}` is CoT;
`{answer, reasoning}` is decoration. That is why every schema in 04 puts `reasoning`
first.

## The variants, quickly

| Variant | What it is | Our verdict |
|---|---|---|
| Zero-shot CoT | "think step by step" in the prompt, free-form thinking before the answer | Works, but unstructured thinking in a *structured-output* call tends to leak into or break the JSON. Not used raw. |
| Structured CoT | A required `reasoning` field **first** in the output schema, with a description saying what to think about | **What we use.** The schema gives thinking a place and a size; the JSON stays intact. |
| Few-shot CoT | Show worked examples with their reasoning | Strongest for exotic tasks; costs many tokens **per call, forever**. Our tasks (describe / split / explain) are common enough that models know the genre. Reserve for a prompt that evals show failing. |
| Plan-then-execute | A separate LLM call produces a plan the next call consumes | We do this **once**, structurally: the block plan is a committed thinking artifact the explainer consumes. Eregna v2 runs a whole visible reason→frame→chapters cascade; we dropped it because traversal removed the decisions it was thinking about. |
| Reasoning models | Models trained to think in a hidden channel before answering (o-series, gpt-5 family, R1, GLM/Kimi thinking modes) | If enabled, it *replaces* manual CoT — then our `reasoning` field shrinks to a one-line summary slot. Do not stack long manual CoT on top of a thinking mode: it doubles cost and the visible field just paraphrases the hidden one. Decide per model at config time; beware reasoning tokens leaking into structured output (a known GLM/Kimi + JSON-mode quirk — see Eregna v2 fixes). **And never set completion caps around a thinking mode**: hidden reasoning consumes the cap before any content (observed live with gpt-5-mini — 700 of 700 tokens on reasoning, empty output). Tune spend via `MODEL_OVERRIDES` (e.g. `reasoning_effort`), never via `max_tokens` (backend/02). |

## The right CoT budget (the actual craft)

CoT is not free: it is output tokens, the expensive and slow kind. The craft is
matching thinking length to decision difficulty:

```
trivial decision  → no CoT            (block text: the block is already chosen;
                                       2-4 sentences of prose IS the output)
one real decision → 1-3 sentences     (block plan: where are the seams?)
                                      (intro: what matters about this node?)
many decisions    → staged calls,     (nothing in MVP; Eregna v2's planner
                    CoT per stage      cascade is the reference pattern)
```

Two failure modes to avoid, both observed in Eregna's iterations:

- **Too little:** small model asked for line ranges with no reasoning field commits to
  the first numbers it types, then rationalizes. First-attempt validation failures go
  up measurably.
- **Too much:** a 300-token `understanding` field before every tiny answer. On a
  35-call tour that is ~10k output tokens of thinking — real money and latency for
  decisions that needed one sentence. Eregna could afford it: its planner ran **once
  per session**. Ours runs per stop. Budget accordingly.

## Where CoT lives in this project — exact placement

| Call | CoT | Why this much and no more |
|---|---|---|
| Intro | `reasoning: str` — 1-2 sentences, "your private read of the node" | One soft decision (what to emphasize). One sentence of grounding cuts generic filler intros. |
| Block plan | `reasoning: str` — ordered: structure → seams → **why this many blocks**; then `block_count: int`; then `blocks` | The one real decision in the system. Forcing a structural read before numbers is the difference between meaning-seams and arithmetic-seams; forcing the count to be justified *then committed as a field* (validator checks `len(blocks) == block_count`) is what keeps the ranges from drifting away from the model's own plan. |
| Block text | **none** | No decision left — range, focus, and the planner's description are inputs. Adding CoT here would be pure cost. |

Supporting rules that make it work:

- `reasoning` fields carry a schema `description` saying **what to think about** —
  an unguided reasoning field degenerates into restating the input.
- **The commitment field.** `block_count` sits *between* reasoning and blocks in the
  schema. The model justifies a count, states it, and only then writes ranges — and a
  code-side check enforces that the ranges honor the stated count. This is the
  cheapest anti-drift device we know: one integer field plus one validator line. Use
  the pattern anywhere a model must derive a number and then produce that many things.
- Prompt rules ban meta-talk in user-facing fields, so thinking never leaks to the
  popup. The field boundary is the privacy boundary.
- We **log** reasoning into the session (it rides `NodeSteps` generation and lands in
  the eval fixtures) but never render it in MVP. When a block plan is bad, the logged
  reasoning usually tells you whether the model misread the code or read it fine and
  split it badly — different fixes.
- Temperature stays low where CoT feeds numbers (block plan, 0.2): thinking varies,
  ranges shouldn't.

## Visible thinking (Eregna v2 did it — we don't, yet)

Eregna renders its planner's reasoning as a user-facing "▶ Reasoning" disclosure, which
means the reasoning must be *written for the visitor* — that changes its style and
doubles its job (think + communicate). Our reasoning is private, so it can stay
terse and mechanical. If we later show a "why this split?" affordance in the UI, the
lesson from Eregna applies: **a field that users see needs its own prompt rules**
(plain language, no keys, no self-reference) — do not just flip the visibility bit on
a private field.

## One-paragraph summary (the takeaway)

Put a small, required, described `reasoning` field **first** in the schema of any call
that makes a real decision; give it a sentence budget matched to the decision; keep it
out of user-facing text; log it for debugging. Skip CoT entirely where the decision has
already been made by an earlier stage or by code. On models with native thinking modes,
turn manual CoT down, not up.
