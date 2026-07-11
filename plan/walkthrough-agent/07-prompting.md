# 07 — Prompting

The exact prompts for the three call types, and — because you asked to learn from this
file — the reasoning behind every part. Prompts live in `prompts.py` as
`ChatPromptTemplate` constants (see "Templates" below); **this doc is canonical: change
it first, then the code, then bump `PROMPT_VERSION`.**

> **Revision 2 (2026-07-11).** Four changes against revision 1, all argued in Part 3:
> a GLOSSARY layer (the model must know what a *group* is before it meets one), the
> intro now reads docs **and** code (code only when docs are absent), the block text
> now sees docs + full code but explains only its range, and the block plan commits to
> a justified `block_count` and writes a one-sentence `description` per block.
> This revision is `PROMPT_VERSION = "2"` and (schema changes) `SCHEMA_VERSION = "2"`.

---

## Part 1 — Anatomy of a prompt (the lesson)

Every prompt we send has the same six layers, in the same order:

```
1. ROLE        who the model is, in one sentence, scoped to ONE job
2. GLOSSARY    what V-NOC's words mean — node kinds and the three group kinds
3. RULES       numbered, testable behavior constraints
4. OUTPUT      what shape comes back (reinforces the bound schema in words)
5. CONTEXT     the data, in labeled, delimited sections   ← the only part that varies
6. TASK        one imperative sentence: do the job now
```

Why this order, and why it matters more on small models:

- **Stable text first, variable text last.** Layers 1–4 are identical for every call
  of a type. Providers cache prompt prefixes; identical prefixes make every call after
  the first cheaper and faster. But the bigger reason is attention: models weight the
  beginning (instructions) and the end (task) most reliably — so rules go up top and
  the "go" goes at the bottom, with bulky context in the middle.
- **The glossary defines our words before we use them.** "Node", "call", "stop", and
  above all "group" are V-NOC words, not the world's. A small model that meets
  `grouped under "Validation helpers"` with no definition guesses from generic
  training — it may narrate the group as a class, a module, or a code scope. One
  stable paragraph defining the node kinds and **all three group kinds** (structure
  group, code-element group, call group) kills that failure class at the root. It
  lives in the stable prefix, so after the first call it is effectively free.
- **Rules are numbered and each is testable.** "Be helpful and clear" is not a rule —
  you can't check it. "Never mention line numbers in the text" is a rule — an eval can
  grep for it. When a rule fails in output, you know which number to strengthen.
- **The output layer repeats the schema in prose.** The schema is enforced by
  structured output anyway; saying it again in words ("you will return reasoning,
  then block_count, then blocks") measurably reduces malformed attempts on small
  models — they read the words more reliably than they infer from a JSON Schema.
- **The output layer must say the word "JSON" literally.** Not style — a provider
  requirement: OpenAI's `json_object` response format **rejects the request with a
  400** ("'messages' must contain the word 'json' in some form") when no message
  contains it. Miss this and *every* call fails before generating a token, the retry
  fails identically, and the whole tour ships as deterministic fallbacks (observed
  live, 2026-07-11). So every OUTPUT line reads "You return one JSON object: …", and
  a prompt unit test greps every system prompt for "JSON".
- **Context sections are labeled and delimited** (`### code`, `### documentation`).
  Small models blur adjacent sections; headers act as anchors the model can "look up"
  instead of re-reading. Never interleave instructions inside context — instructions
  live in layers 1–4 only, so context can never *look like* an instruction
  (prompt-injection hygiene, even though our context is our own graph).
- **A section with nothing to show is omitted entirely** — header and all, never an
  empty `### documentation`. An empty section teaches the model that empty is normal;
  a missing one keeps the map honest. Rules that depend on a section's presence are
  written conditionally ("if documentation is provided…").
- **One job per prompt.** The moment a prompt says "also", split the call. This is the
  whole 05 design restated at prompt level.

### Templates are LangChain objects, not f-strings

Revision 1 said "plain string builders, no engine". That was one convenience too far —
the LangChain way costs nothing and buys three checks:

```python
INTRO_PROMPT = ChatPromptTemplate.from_messages([
    ("system", INTRO_SYSTEM),   # layers 1-4 — one module constant, stable
    ("human",  INTRO_USER),     # layers 5-6 — placeholders for NodeContext fields
]).partial(persona=PERSONA, glossary=GLOSSARY)
```

- **Missing variable = hard error at render time.** An f-string builder happily prints
  `None` into the prompt and nobody notices until an eval regresses. `format_messages`
  raises.
- **The prompt's data needs are code, not convention.** Tests assert
  `set(INTRO_PROMPT.input_variables)` against the `NodeContext` fields 06 promises —
  the 06↔07 contract becomes a unit test.
- **The stable prefix exists exactly once.** `PERSONA` and `GLOSSARY` are `.partial()`
  bindings; four templates share them and cannot drift apart.

Boundary rule: templates render to two strings (system, user) **inside** `prompts.py`;
`structured_call(call_type, schema, system, user)` keeps its string signature. The
`FakeLLM`, logging, and the transport never learn about LangChain templates. Structured
output stays `with_structured_output(schema, method="json_mode")` (backend/02).
One more contract: the Pydantic schemas' `Field(description=...)` strings are part of
the prompt — JSON mode sends them with the schema. Write them with the same care as
rules; 08 relies on this for steering `reasoning`.

House style rules (apply to all prompts):

- Second person, present tense ("You write…", not "The assistant should…").
- No politeness padding, no "please". Tokens are attention; spend them on constraints.
- Numbers over adjectives: "2–4 sentences", never "brief".
- Forbid the failure modes we've seen, by name (see each prompt's rule list) — small
  models need the *don'ts* spelled out.
- Markdown in user-facing fields: `inline code` for identifiers and short expressions;
  a fenced block only for code the user cannot already see on screen; no headings, no
  links, no images. (This folds fix 13's renderer note into the contract —
  the `PROMPT_VERSION` bump this revision carries is the bump that note waited for.)
- **Every user-facing field is complete sentences and complete paragraphs — nothing is
  ever truncated by machinery.** No call sets `max_tokens` at all: a cap sized for
  one model family starves another — reasoning models spend the whole cap on hidden
  thinking before writing a word (observed live with gpt-5-mini: 700 of 700 tokens on
  reasoning, empty content, every intro degraded — backend/02). Length lives here, in
  the rules, as **stated targets the model aims for** ("Aim for 2–4 sentences"),
  never as something a cap or validator enforces. Enforcement belongs only where a
  validator can check and retry cleanly (block counts, line ranges, the ≤ 100-char
  `focus` UI label) — never on prose.

---

## Part 2 — The prompts

Placeholders in `{braces}` are filled from `NodeContext` (06). Two shared constants
head every system prompt:

`{persona}`:

```
You are the narrator of a guided code walkthrough inside V-NOC, a graph-based IDE.
The user watches nodes on a canvas while your text appears in a popup.
Write for a developer seeing this codebase for the first time. Grade-10 English:
short sentences, plain words, technical terms only when the code forces them.
Markdown: `inline code` for identifiers; a fenced block only for code the user
cannot already see; no headings, no links, no images.
```

`{glossary}`:

```
V-NOC words, so you read the context correctly (never explain them to the user):
- project, folder, file: the repository's structure, shown as nodes on a canvas.
- class, function: code elements parsed from the source. They own real line ranges.
- call: one call site inside a body. It points at the function or class it invokes
  (its target); a call stop shows the target's code in the caller's context.
- group: a box a user drew on the canvas to organize nodes. Groups are visual
  only: they are not code, they own no lines, and they never get their own stop.
  The three kinds are structure group (holds folders and files), code-element
  group (holds classes and functions), and call group (holds call sites).
  Grouped under "X" in a child list means X is such a box — nothing more.
```

### 2.1 Intro — full stop (system)

```
{persona}

{glossary}

Your job for this message: introduce ONE node from the outside, before the tour
steps into it.

Rules:
1. Aim for 2-4 sentences. First sentence: what this {node_type} IS and what it
   is for.
2. Explain from outside: purpose, role among its siblings, what it contains or
   calls — by name only. Do not walk through how the code works; the tour does
   that next, block by block.
3. Ground every claim in the provided context. If documentation is provided, it
   is the authority for WHAT this node is for; use the code only to confirm.
   If no documentation is provided, read the code and describe what it actually
   does — never guess past it.
4. Never invent names, parameters, or behavior not visible in the context.
5. Do not mention: line numbers, file paths, "the context", "the documentation",
   these rules, or that you are an AI.

You return one JSON object: reasoning (1-2 sentences, your private read of the
node — not shown to the user), then intro (the popup text).
```

### 2.1 Intro — full stop (user)

```
### node
{header}
{description}

### documentation (may be truncated)
{docs_excerpt}

### code (may be trimmed)
{intro_code}

### inside it
{child_lines}

### where we are in the tour
{tour_position}
Parent: {parent_line}

Introduce this node now.
```

Presence rules (the omission rule from Part 1, applied):

| Section | Present when |
|---|---|
| `### documentation` | the node has attached docs (`docs_excerpt` non-empty) |
| `### code` | the node owns code — `intro_code` is the trimmed form from 06 (full when ≤ 80 lines, else head + `[… trimmed]` marker). Containers (project/folder/file) never have it |
| `### inside it` | the node has children |
| `Parent:` line | the node has a parent in the tour |

So a documented function shows docs **and** code; an undocumented one shows code only —
exactly the grounding ladder rule 3 describes. A container with docs shows docs and
children; a bare folder shows only children.

### 2.2 Intro — contextual stop (system)

Same `{persona}` + `{glossary}`, then:

```
Your job for this message: explain ONE call site. The body being called was
already explained earlier in the tour (or is external); do NOT re-explain it.

Rules:
1. Aim for 2-3 sentences, in the caller's context: what goes in, what comes
   back, and why the caller needs it at this point.
2. If a reference is provided ("explained at stop N"), mention it naturally:
   "covered earlier", "as we saw at stop N".
3. Never describe the callee's internals. Never invent parameters or return
   values not visible in the provided context.
4. Same bans as always: no line numbers, no paths, no rules, no AI talk.

You return one JSON object: reasoning (private), then intro (the popup text).
```

User message: `### call site` header + description, `### caller` caller_line,
`### earlier` first_seen_ref (omitted when the target is external), then
`Explain this call now.`

### 2.3 Block plan (system)

```
{persona}

{glossary}

Your job for this message: split ONE node's code (a function or class) into
sequential blocks for a step-by-step explanation. You are planning the pauses,
not explaining.

Rules:
1. Think in reasoning, in this order: (a) what the code's overall structure is,
   (b) where the natural seams are — setup / validation / core work / result /
   error handling, (c) how many blocks that gives and WHY that count, within
   {min_blocks}-{max_blocks}. Only after that, write the blocks.
2. block_count is the number your reasoning justified. blocks must contain
   exactly block_count entries. No other count passes validation.
3. Use the absolute line numbers exactly as shown in the code. Every block must
   lie inside lines {start_line}-{end_line}. Blocks are ordered, must not
   overlap, and together must cover the logic. Small glue lines may be skipped,
   big holes may not.
4. Never split mid-statement, mid-if, or inside one logical operation.
5. focus: at most 100 characters, what the block DOES ("validate the card
   fields"), not what it contains ("lines with ifs"). It becomes the step's
   title in the tour outline — the user reads it.
6. description: one complete sentence to the narrator who will explain this
   block — what the block does and why the code needs it. The user never sees
   it, but write it whole; a later call reads it as its brief.

You return one JSON object, keys in order: reasoning, block_count, blocks
(each block with start_line, end_line, focus, description).
```

### 2.3 Block plan (user)

```
### node
{header}
{description}

### code
{numbered_code}

Split into {min_blocks}-{max_blocks} blocks now.
```

No docs here — deliberate; see Part 3. On retry after validation failure, one line is
appended:

```
Your previous answer failed validation: {validator_message}
Fix exactly that and answer again.
```

### 2.4 Block text (system)

```
{persona}

{glossary}

Your job for this message: explain ONE block of a node the user is looking at.
The block's lines are highlighted for them right now.

Rules:
1. Your subject is ONLY lines {block_start}-{block_end}. The full code and the
   documentation are given so you understand the whole before explaining the
   part — never explain lines outside your block.
2. Aim for 2-4 sentences. Explain what the block does and why the code needs
   it — intent over syntax. Never narrate line by line ("first it..., then
   it..., then it...").
3. Documentation tells you intent; the code tells you mechanics. If they
   disagree, describe what the code does. Never quote or paraphrase
   documentation sentences into your text.
4. Mention a called function by name only; if it appears in "names in this
   block", you may add its one-line role. Its body is another stop.
5. Do not repeat what previous blocks covered (their summaries are listed).
6. No line numbers in the text (the highlight shows them), no paths, no rules,
   no AI talk.

You return one JSON object with a single key: text (the popup body).
```

### 2.4 Block text (user)

```
### node
{header}

### documentation (may be truncated)
{docs_excerpt}

### code
{numbered_code}

### your block
Lines {block_start}-{block_end}: {focus}
Planner's note: {block_description}

### previous blocks covered
{previous_block_lines}

### names in this block
{child_lines_in_range}

Explain your block now.
```

`{previous_block_lines}` is one line per finished block, `lines A-B: focus —
description` — the plan's own words, not the generated texts (see Part 3).
`### documentation` and `### names in this block` follow the omission rule.

---

## Part 3 — Design notes worth keeping

**Why the glossary is in every prompt, not just where groups appear.** Deciding
per-call whether the glossary is needed is itself a bug surface (a child line with
`grouped under` slips through, the model improvises). Constant prefix = cacheable, so
the marginal cost of always including it is near zero, and the eval for it is a
one-line snapshot grep: every system prompt contains "code-element group".

**Why the intro now sees code (changed from revision 1).** Revision 1 gave the intro
no code, betting on `description` + docs. Reality on the server: `description` is
frequently blank and most nodes have no attached docs — an intro grounded in nothing
produces exactly the generic filler we banned ("this function handles part of the
flow"). The ladder is now: docs are the authority when present, code is the evidence
always, and rule 2 keeps the zoom level ("from outside") even though code is visible.
The 06 trim rule keeps the budget honest.

**Why the block text now sees docs (changed from revision 1).** Revision 1 kept docs
away from the explainer fearing doc-paraphrase. The user-visible narration is where
intent matters most, and intent lives in docs; starving the detail narrator of it was
the wrong trade. The failure mode is now handled by rule 3 (docs = intent, code =
mechanics, never quote) plus an eval: n-gram overlap between `docs_excerpt` and
generated `text`.

**Why the block plan still gets no docs.** Its one decision is structural — seams live
in the code. Docs tempt doc-shaped splits ("the README describes three phases") that
the line validator then rejects; the retry budget is better spent elsewhere.

**Why `block_count` is a schema field.** Field order is reasoning → block_count →
blocks: the model commits to the justified count *immediately after* justifying it and
*before* typing any ranges — a small model that goes straight to ranges tends to drift
from its own stated plan. The validator cross-checks `len(blocks) == block_count`, so
the commitment is enforced, not hoped for. (08 explains why order inside the schema is
the whole trick.)

**Why blocks gained `description`.** The planner is the only call that reads the whole
node structurally; the per-block explainer calls are otherwise independent of each
other. `description` hands the planner's understanding down (a steer for the
explainer: "Planner's note") and sideways (previous-block summaries at higher fidelity
than the 100-char `focus`, which is a UI title, not a summary). Cost: ~25 output
tokens per block, ≤ 6 blocks. `focus` stays user-facing and short — the frontend
renders it in the outline row (`OutlineRow.tsx`) and as the step title.

**Why `reasoning` is in the schema but the ban list forbids meta-talk.** The reasoning
field gives the model a place to think (08 explains why that helps); the rules make
sure thinking never leaks into user-facing text. Separation by *fields*, not by hoping.

**Why the block plan is told "you are planning the pauses, not explaining".** Small
models asked for structure tend to start explaining (wrong artifact). Naming the
anti-goal cuts this failure sharply.

**Why "intent over syntax" and the anti-example in rule 2 of block text.** The single
worst failure mode of cheap models explaining code is the line-by-line paraphrase
("first it assigns x…"). One explicit ban with the pattern shown is the cheapest fix
we know.

**Why bounds are injected as numbers** (`{min_blocks}`, `{max_blocks}`) instead of
"a few": the same prompt text serves a 10-line and a 150-line function, and the
validator enforces exactly what the prompt promised. Prompt and validator must always
quote the same numbers — they are generated from the same `VisitNode`.

**Versioning.** `PROMPT_VERSION` (stamped on every session) bumps on any change to
this file's Part 2 — this revision makes it `"2"`. `SCHEMA_VERSION` bumps
independently on output-shape changes (04) — `block_count` + `description` make it
`"2"` too. Quality regressions trace to exactly one of the two.
*Post-implementation fix (2026-07-11, same day):* the OUTPUT lines gained the literal
word "JSON" after the live 400s described in Part 1 — that text change makes
`PROMPT_VERSION = "3"` (fixes/16).
*Second fix (2026-07-11, later):* sentence counts became stated targets ("Aim for
2–4 sentences") and completion caps were removed entirely after gpt-5-mini spent a
700-token cap wholly on hidden reasoning — `PROMPT_VERSION = "4"` (fixes/17).

**Evals** (lightweight, MVP-honest): keep 5–10 exported sessions as fixtures; after a
prompt change, re-run them and diff. Automatable checks: validator pass rate on first
attempt, `block_count` mismatch rate, block text length bounds, banned-phrase greps
("line 12", "as an AI", "the context"), repetition between sibling blocks (n-gram
overlap), doc-paraphrase overlap (docs_excerpt vs text), the glossary snapshot
grep, and the JSON-word grep (every system prompt contains "JSON" — the 400 guard).
Prose quality stays a human read of the diff.
