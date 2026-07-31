# Document 02 — Prompt, Sections, and Call-Edge Grounding

What a document call sees and the fixed skeleton it must fill. The section list
is the user's spec, made structural: *what it is, why, usage, role in the
overall project, and how the children interact* — overview style, angled by
intent but never bent by it.

## The output shape

```python
class DocumentOut(BaseModel):
    reasoning: str                  # private: the model's read of the node (CoT-first)
    title: str                      # ≤ 60 chars, names the node's job, not its path
    sections: DocSections

class DocSections(BaseModel):
    what_it_is: str                 # 2-4 sentences: the thing, in plain words
    why_it_exists: str              # the problem it solves / why not elsewhere
    usage: str                      # how callers use it: entry points, typical flow
    role_in_project: str            # where it sits in the bigger picture
    how_parts_work_together: str | None = None   # containers/classes only
```

**Why structured sections instead of free markdown with headings.** Three
reasons. Validation becomes field checks instead of markdown parsing ("is
`usage` empty?" vs regexing headings). Rendering stays ours — the frontend
assembles the markdown with house heading styles, so every doc in the project
looks the same. And the empty-is-omitted rule works per section: a leaf function
has no `how_parts_work_together`, and `None` means the section *doesn't render*
— no "N/A" filler, the same no-empty-tags discipline as the serializer.

## The context (factory preset `document_node`)

| Ingredient | Source | Cap |
|---|---|---|
| own numbered code (leaves) or child summaries (containers) | code service / fresh-summary override map (describe/01 mechanism, shared) | code ≤ 80 lines full else head+marker |
| fresh descriptions of children | this run + stored | 20, one-liners (sentence 1) |
| child docs written **this run** | title + `what_it_is` only | 10 |
| existing attached docs on the node | excerpt | ~600 tokens (the v2 doc cap) |
| **call edges among the node's descendants** | the call graph TerminusDB already stores | 30 edges, rendered `<call from="charge" to="validate_card"/>` |
| parent name + kind | graph | one line |
| `<user_intent>` | args | one sentence |

The call-edge block is the new ingredient and it exists for exactly one section:

**`how_parts_work_together` must be grounded in edges, not vibes.** "The
children interact" is where an ungrounded model writes plausible fiction —
inventing orchestration that isn't there. The graph already *knows* who calls
whom (the call nodes the parser built); serializing those edges into the context
turns the section from creative writing into reporting. The prompt rule:
*describe only interactions visible in the call list or the code; if the
children don't interact, say they're independent — that's a finding, not a
failure.* The factory gains one `Include` flag (`calls: bool`) — a small,
planned extension, not a redesign.

## The prompt (registry: `document.node`, own version)

```
Write the overview documentation for ONE {node_type}, for a developer meeting
it for the first time. Overview style: explain the thing, don't tour the code
line by line (walkthroughs do that).

Sections and their jobs:
- what_it_is       — plain words first sentence; no jargon before it's earned.
- why_it_exists    — the problem it solves; what would be worse without it.
- usage            — how callers actually use it: entry points, typical call
                     flow, what goes in and comes out. Ground in real
                     signatures; never invent parameters.
- role_in_project  — one level up: what depends on it, what it depends on,
                     where it sits in the flow you can see in the context.
- how_parts_work_together (only if children are provided) — the story of a
                     typical flow through the children, grounded ONLY in the
                     call edges and code provided. Reference child docs by
                     their titles. If parts are independent, say so plainly.

Intent: if <user_intent> is present, weight your emphasis toward it where the
node is genuinely relevant — but every section stays truthful and complete.
The intent chooses emphasis, never content.

Grounding (senior to everything above): every name, parameter, and interaction
must appear in the provided context. No line numbers, no file paths, no
meta-talk, no AI-talk.
```

## Validation (code, before writing)

- required sections non-empty (except the optional one); per-section length
  windows (no one-line `why_it_exists`, no 800-word `what_it_is`);
- **anti-invention grep**: every backticked identifier must appear in the
  context (code, child names, call edges) — the MVP's cheapest and most
  brutal check, inherited;
- interaction claims: every "X calls/uses Y" pair in
  `how_parts_work_together` where both X and Y are child names must match a
  provided call edge (string-level check; crude, catches the worst lies);
- child-doc references must match titles written this run.

Retry once with validator messages; second failure → no doc, item `failed`
(the anti-poison rule, document/01).

## Intent examples (what "lens, not filter" means here)

| user_query | Effect on the doc |
|---|---|
| "" | balanced overview, all sections even |
| "how do retries end up double-charging" | `usage` and `how_parts_work_together` spend their words on the retry path and the charge/refund interplay; `what_it_is` unchanged |
| "is this safe to delete" | `role_in_project` leads with dependents and callers; nothing else shrinks below its length floor |

Stored on the run (`ToolRun.user_query`) so evals can ask the greppable
question: did intent-angled docs stay complete? (Assert all sections present
regardless of query — the same style of check as "no `<user_intent>` in block
plans".)
