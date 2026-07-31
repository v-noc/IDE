# Context Engineering 02 — The Unified Context Factory

One builder for every graph-context block in the system. You tell it *which node*,
*how far up*, *how far down*, and *what to include at each level* — it loads the
data through the existing repositories, applies the caps, and renders the tags.

## The problem it solves

Today, `app/walkthrough/context.py` hand-builds each format: `_parent_line`,
`_child_lines`, `_docs_excerpt`, `trim_for_intro` — all correct, all capped, but
all welded to the walkthrough's specific shapes. The chat agent needs *almost* the
same blocks (attached-node enrichment, project header), a future describe tool
needs another variant, and every new consumer would re-implement loading, capping,
and trimming. That is how budgets drift and formats fork.

**Decision: one declarative spec, one factory, presets for consumers.**

## The spec — say what you want, not how to build it

```python
# app/agent/context/factory.py

class Scope(BaseModel):
    """How far to walk in one direction."""
    levels: int = 0                  # 0 = don't include; 1 = direct; 2 = grandkids…
    all: bool = False                # walk to the end (root upward / leaves downward)
                                     # "all" is still capped by max_nodes — see Caps

class Include(BaseModel):
    """What to render for nodes at some position."""
    description: bool = True         # the stored one-liner
    docs: bool = False               # attached docs excerpt (token-capped)
    code: bool = False               # numbered code (line-capped + intro-trim rules)

class Caps(BaseModel):
    siblings: int = 10
    children_per_level: int = 20
    max_nodes: int = 60              # hard ceiling for "all" walks — by construction
    doc_tokens: int = 600
    code_lines_full: int = 80        # ≤ this → full code; else head + honest marker
    code_lines_head: int = 60

class ContextSpec(BaseModel):
    parent: Scope = Scope()          # upward walk
    children: Scope = Scope()        # downward walk
    siblings: bool = False
    self_include: Include = Include()
    parent_include: Include = Include()          # docs/code default False upward
    children_include: Include = Include()        # per-child description; docs/code opt-in
    caps: Caps = Caps()
```

Usage:

```python
factory = ContextFactory(repos)                    # the SAME Repositories the routes use
block = await factory.build(node_id, spec)         # → rendered tag block (xml.py)
```

This is exactly the knob set Yared asked for: parent by depth or all, children by
depth or all, and per-direction choice of description / docs / code — as data, not
as new functions per consumer.

## Presets — the guardrail on top of the freedom

```python
# named, versioned, unit-tested for worst-case token budget
PRESETS = {
    "project_header":  ContextSpec(children=Scope(levels=1),          # optional top-level one-liners
                                   children_include=Include(description=True)),
    "attached_node":   ContextSpec(parent=Scope(levels=1), siblings=True,
                                   children=Scope(levels=1),
                                   self_include=Include(description=True, docs=True, code=True)),
    "walkthrough_intro": …,          # the MVP intro context, expressed as a spec
}
```

**Decision: consumers pick presets; only presets are used in production paths.**
The spec being fully general is for *building* presets and for experiments — if
every call site invented its own spec, budgets would drift exactly the way
Principle 2 forbids. A new context shape = a new named preset + its budget test.
(This is the one place this plan deliberately narrows the "choose anything"
idea: full freedom at the API, discipline at the call sites — you get both.)

## Inside the factory — loader and renderer, split

```
build(node_id, spec)
  1. LOAD  — batched repo reads through Repositories/UoW:
             ancestors (parent chain), siblings, descendants level by level,
             docs for whichever Include asks, code bounds for code nodes.
             Groups are flattened (transparent), same as the traversal loader.
  2. SHAPE — apply caps: slice sibling/child lists (+ "…and N more" line),
             stop "all" walks at max_nodes, trim code, cap doc excerpt.
  3. RENDER — xml.py turns the shaped tree into tags. No caps here; by the
             time rendering runs, the data already fits.
```

**Why the split.** The loader is testable against fixtures without token math;
the renderer is testable with zero DB. And the loader is where a future
performance pass lives (one WOQL path query per direction instead of per-level
reads) without touching a single consumer.

**Why it reads through the existing repos.** `ContextFactory(repos)` takes the
`Repositories` container from the request's `ProjectUoW` — so context automatically
respects branch (`X-Vnoc-Branch`) and ref pinning, free of charge. A tool running
against a pinned commit passes its pinned repos; the enrichment middleware passes
head repos. Same factory, correct data.

## Depth semantics (precise, because "depth" caused MVP bugs)

- `parent: Scope(levels=1)` → the direct parent, rendered with its description.
  `levels=2` adds the grandparent as a one-liner chain. `all=True` → up to the
  project root (bounded — trees are shallow upward).
- `children: Scope(levels=1)` → direct children as one-liners. `levels=2` nests
  one more level *inside* each child tag. `all=True` → whole subtree, stopped at
  `caps.max_nodes` with an honest `…and N more` — never silently.
- Call nodes count as children of their caller (they render their **target's**
  name and description) — matching how the walkthrough traversal treats calls.

## Migration path for `app/walkthrough/context.py`

Phase 3 does **not** rewrite the walkthrough. The factory ships for the agent's
needs (`project_header`, `attached_node`). Then, one context at a time, the
walkthrough's builders become presets (`walkthrough_intro`, `walkthrough_block`)
with before/after prompt fixtures proving the rendered output is equivalent. The
MVP's zoom levels, field choices, and budgets are kept as-is — only the *rendering
and loading* converge on the factory.

**Why not rewrite immediately:** the walkthrough works and has evals; converging
formats is a quality project with its own verification, not a prerequisite for
shipping the chat agent.
