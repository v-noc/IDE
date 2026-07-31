# Document 01 — Tool Spec

The overview writer. Same traversal, same direction, same artifact as describe —
but each call produces a full markdown document in a fixed overview skeleton,
and the user's intent is welcome here (as a lens, with the same seniority rules
as walkthrough narration).

## The spec

```python
class DocumentArgs(BaseModel):
    node_id: str = Field(description="The attached node to document from. Children "
                                     "are documented too, down to depth.")
    depth: int = Field(0, ge=0, le=5, description="Levels below the node to also "
                                     "document. 0 = just this node (the common case).")
    user_query: str = Field("", description="The user's goal, one plain sentence in "
                                     "their words. Empty if no particular angle.")
    overwrite: bool = Field(False, description="Regenerate agent-written docs. "
                                     "Never touches human-written docs.")

SPEC = ToolSpec(
    name="document_nodes",
    description="Write an overview document for a node (and optionally its "
                "children): what it is, why it exists, how to use it, its role "
                "in the project, and how its parts work together. The biggest "
                "LLM outputs in the system — an estimate is shown for approval.",
    input_model=DocumentArgs,
    kind="task",
    confirmation="over_threshold",       # low bar in practice: doc calls are heavy
    render="run_checklist",
    handler=DocumentTool(),
)
```

**Why `depth` defaults to 0 here but 1 elsewhere.** Tours and descriptions get
their value from breadth; a *document* is usually wanted for one thing the user
is staring at. Subtree documentation ("document everything under `core/`") is
the explicit, confirmed choice, not the accident.

## Post-order pays twice here

1. **Parents cite children.** `PaymentService`'s doc can reference the `charge`
   and `refund` docs *by title* because those docs exist by the time the parent
   is written — dead links are impossible by construction.
2. **The children-interaction section has fresh material**: child docs' purpose
   sections + fresh descriptions + the call edges among children (document/02) —
   the parent doc's hardest section is grounded, not improvised.

## `estimate()`

Same shape as describe (exact call count, skip counting, WOQL depth cap on the
knob), plus a size-aware label — "3 docs · 3 large calls (~2k tokens each)" —
because a doc call costs several times a describe call and the label should say
so. One extra field in `knobs`:

```python
knobs["undescribed_children"] = 14     # when > 0, the confirm card hints:
                                       # "14 children have no descriptions —
                                       #  running describe first improves this doc"
```

**Why a hint and not an automatic chained run.** Chaining tools inside a tool
breaks the one-estimate-one-confirmation contract (the user would approve one
cost and pay two). The agent already suggests describe-first (the quality
gradient); this hint is the same suggestion at the moment of decision, and the
user stays in charge.

## `run()` — the loop

Identical skeleton to describe (pin → post-order plan → skip check → context →
`structured_call("document", …)` → validate → write → persist → patch), with the
differences:

- context preset `document_node` includes docs excerpts and call edges
  (document/02);
- write path: replace-or-attach on the node's `documents[]` via the existing
  `DocumentRepo`, tagged per shared/03 — regeneration replaces the previous
  agent doc, never piles up, never touches human docs;
- the doc's first line names its commit: `> Generated against <short-sha> —
  <date>` — a reader always knows which version of the code it describes;
- fallback: **no doc written** — same anti-poison rule as describe; a wrong doc
  on a node is worse than no doc, because docs feed future intro contexts
  (walkthrough) and future document runs (this tool's own parent calls);
- `preview` on the run item = the doc's title line, so the checklist doubles as
  a table of contents while it fills.

## v2 seam (not built now)

Two-stage outline → sections for very large nodes — the MVP's plan/commit
pattern (`section_count` as the commitment field) is the ready-made shape.
Trigger: dogfooding shows single-call docs rambling or truncating on nodes above
~300 lines or ~20 children.
