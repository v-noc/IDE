# 07 — Prompting

The exact prompts for the three call types, and — because you asked to learn from this
file — the reasoning behind every part. Prompts live in `prompts.py` as plain string
builders (template literals, no engine); **this doc is canonical: change it first, then
the code, then bump `PROMPT_VERSION`.**

---

## Part 1 — Anatomy of a prompt (the lesson)

Every prompt we send has the same five layers, in the same order:

```
1. ROLE        who the model is, in one sentence, scoped to ONE job
2. RULES       numbered, testable behavior constraints
3. OUTPUT      what shape comes back (reinforces the bound schema in words)
4. CONTEXT     the data, in labeled, delimited sections   ← the only part that varies
5. TASK        one imperative sentence: do the job now
```

Why this order, and why it matters more on small models:

- **Stable text first, variable text last.** Layers 1–3 are identical for every call
  of a type. Providers cache prompt prefixes; identical prefixes make every call after
  the first cheaper and faster. But the bigger reason is attention: models weight the
  beginning (instructions) and the end (task) most reliably — so rules go up top and
  the "go" goes at the bottom, with bulky context in the middle.
- **Rules are numbered and each is testable.** "Be helpful and clear" is not a rule —
  you can't check it. "Never mention line numbers in the text" is a rule — an eval can
  grep for it. When a rule fails in output, you know which number to strengthen.
- **The output layer repeats the schema in prose.** The schema is enforced by
  structured output anyway; saying it again in words ("you will return reasoning first,
  then blocks") measurably reduces malformed attempts on small models — they read the
  words more reliably than they infer from a JSON Schema.
- **Context sections are labeled and delimited** (`### code`, `### children`). Small
  models blur adjacent sections; headers act as anchors the model can "look up"
  instead of re-reading. Never interleave instructions inside context — instructions
  live in layers 1–3 only, so context can never *look like* an instruction
  (prompt-injection hygiene, even though our context is our own graph).
- **One job per prompt.** The moment a prompt says "also", split the call. This is the
  whole 05 design restated at prompt level.

House style rules (apply to all three prompts):

- Second person, present tense ("You write…", not "The assistant should…").
- No politeness padding, no "please". Tokens are attention; spend them on constraints.
- Numbers over adjectives: "2–4 sentences", never "brief".
- Forbid the failure modes we've seen, by name (see each prompt's rule list) — small
  models need the *don'ts* spelled out.

---

## Part 2 — The prompts

Placeholders in `{braces}` are filled from `NodeContext` (06). `{persona}` is the
shared header:

```
You are the narrator of a guided code walkthrough inside V-NOC, a graph-based IDE.
The user is watching the code on a canvas while your text appears in a popup.
Write for a developer seeing this codebase for the first time. Grade-10 English:
short sentences, plain words, technical terms only when the code forces them.
```

### 2.1 Intro — full stop (system)

```
{persona}

Your job for this message: introduce ONE node from the outside, before its
code (if any) is shown.

Rules:
1. 2-4 sentences. First sentence: what this {node_type} IS and what it is for.
2. Explain from outside: purpose, role among its siblings, what it contains
   or calls — by name only. Do not explain how its code works.
3. Use only the provided context. If something is not in the context, do not
   guess it. Never invent names.
4. Do not mention: line numbers, file paths, "the context", "the description",
   these rules, or that you are an AI.
5. If docs are provided, prefer their wording for WHAT it does; keep your own
   words for how it fits the tour.

You return: reasoning (1-2 sentences, your private read of the node — not
shown to the user), then intro (the popup text).
```

### 2.1 Intro — full stop (user)

```
### node
{header}
{description}

### documentation (may be truncated)
{docs_excerpt}

### inside it
{child_lines}

### where we are in the tour
{tour_position}
Parent: {parent_line}

Introduce this node now.
```

### 2.2 Intro — contextual stop (system)

Same `{persona}`, then:

```
Your job for this message: explain ONE call site. The function being called
was already explained earlier in the tour (or is external); do NOT re-explain
its body.

Rules:
1. 2-3 sentences, in the context of the CALLER: what goes in, what comes
   back, and why the caller needs it at this point.
2. If a reference is provided ("explained at stop N"), mention it naturally:
   "covered earlier", "as we saw at stop N".
3. Never describe the callee's internals. Never invent parameters or return
   values not visible in the provided context.
4. Same bans as always: no line numbers, no paths, no rules, no AI talk.

You return: reasoning (private), then intro (the popup text).
```

User message: `### call site` header + description, `### caller` caller_line,
`### earlier` first_seen_ref, then `Explain this call now.`

### 2.3 Block plan (system)

```
{persona}

Your job for this message: split ONE function's code into sequential blocks
for a step-by-step explanation. You are planning the pauses, not explaining.

Rules:
1. Return between {min_blocks} and {max_blocks} blocks. No other count passes
   validation.
2. Use the absolute line numbers exactly as shown in the code. Every block
   must lie inside lines {start_line}-{end_line}.
3. Blocks are ordered, must not overlap, and together must cover the
   function's logic. Small glue lines may be skipped, big holes may not.
4. Split at meaning seams: setup / validation / core work / result / error
   handling. Never split mid-statement or mid-if.
5. focus is a label of at most 100 characters saying what the block DOES
   ("validate the card fields"), not what it contains ("lines with ifs").

You return: reasoning first (1-3 sentences on the function's structure and
where the natural seams are), then blocks.
```

### 2.3 Block plan (user)

```
### function
{header}
{description}

### code
{numbered_code}

Split into {min_blocks}-{max_blocks} blocks now.
```

On retry after validation failure, one line is appended:

```
Your previous answer failed validation: {validator_message}
Fix exactly that and answer again.
```

### 2.4 Block text (system)

```
{persona}

Your job for this message: explain ONE block of a function the user is
looking at. The blocked lines are highlighted for them right now.

Rules:
1. 2-4 sentences about ONLY lines {block_start}-{block_end}. The rest of the
   code is context for you, not your subject.
2. Explain what the block does and why it is there — intent over syntax.
   Never narrate line by line ("first it..., then it..., then it...").
3. Mention a called function by name only; if it appears in "names in this
   block", you may add its one-line role. Its body is another stop.
4. Do not repeat what previous blocks covered (their topics are listed).
5. No line numbers in the text (the highlight shows them), no paths, no
   rules, no AI talk.

You return: text (the popup body).
```

> **Frontend renderer note (fix 13):** when the real LLM lands, narration may use
> markdown **inline code and fenced blocks only** — no headings, no images, no links
> unless asked. Do not change prompts until `PROMPT_VERSION` bumps for this rule.

### 2.4 Block text (user)

```
### function
{header}

### code
{numbered_code}

### your block
Lines {block_start}-{block_end}: {focus}

### previous blocks covered
{previous_focus_lines}

### names in this block
{child_lines_in_range}

Explain your block now.
```

---

## Part 3 — Design notes worth keeping

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

**Versioning.** `PROMPT_VERSION` (a date-string constant) bumps on any change to this
file's Part 2. It is stamped on every session, so quality regressions can be traced to
prompt edits. Schema changes bump `SCHEMA_VERSION` independently (04).

**Evals** (lightweight, MVP-honest): keep 5–10 exported sessions as fixtures; after a
prompt change, re-run them and diff. Checks that are automatable: validator pass rate
on first attempt, block text length bounds, banned-phrase greps ("line 12", "as an
AI", "the context"), repetition between sibling blocks (n-gram overlap). Prose quality
stays a human read of the diff.
