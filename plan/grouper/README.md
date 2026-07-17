# Grouper — `group_children`, the First Two-Gate Tool

The third write tool on the v2 harness (after agent-v3's describe/document):
organize a node's children into named groups. The user picks a node whose
child list has outgrown scanning, the agent proposes groups, **the user
reviews the proposal before anything is written**. That last clause is the
new machinery: v2 has one confirmation (approve the *spend*); the grouper
adds a second (approve the *write*). Every future tool whose output deserves
editing before it lands inherits the gate this plan builds.

## The user flow (the whole tool in one story)

1. The user attaches `payments/` (14 children) and asks "organize this" — or
   picks **Group** in the tool picker and hits send.
2. The agent distills intent and calls `group_children`, optionally passing a
   `category` if the user named a dimension ("group them by lifecycle").
3. **Gate 1 — estimate (v2 standard, unchanged).** The card shows the knobs:
   min children **4**, min groups **2**, max groups **6**, the optional
   category, and the honest cost (~2 LLM calls). User tweaks, hits *Create
   groups*.
4. The tool reads the children (names, kinds, first-sentence descriptions),
   and the model proposes: a **dimension** ("grouped by pipeline stage" — the
   explanation the user asked for), named groups with members, and any
   children it left ungrouped, with reasons. A validator checks the proposal;
   invalid → one retry with the errors.
5. **Gate 2 — review (new, harness/03-review-gate).** The run pauses. The
   card flips to *awaiting review*: the dimension line (editable), the groups
   (rename, move members, dissolve), the ungrouped remainder. Nothing exists
   in the graph yet.
6. The user edits or not, hits **Approve** → the tool writes the groups
   through the existing `GroupService`, one commit batch, undo-able. Cancel →
   zero writes, the transcript keeps the proposal as the record.
7. Done face: group pills with counts + the dimension line. The canvas shows
   the new boxes.

## Your idea → the shipped shape (what this plan changes and why)

| The raw idea | The plan's version | Why |
|---|---|---|
| "generate a group and add the items" | **propose first, write only on approve** | Groups are structure — wrong ones are worse than none. Writing then editing means undo paths and flicker; proposing then writing means gate 2 is free of risk. Cleanest write-safety of the three write tools: the run itself is read-only. |
| min children default 4 | `min_children=4` — below it the tool **refuses with a sentence**, not a silent no-op | The agent gets a reason it can relay ("only 3 children — grouping adds a layer without removing any scanning cost"). |
| min 2 / max 6 groups | same defaults, validator-enforced, user-tunable at gate 1 | Matches the mock's steppers (already specced in frontendv2/03). Validator also requires ≥2 members per group — a group of one is an insult to the child. |
| "user might add category feature" | optional `category` free-text arg = the **dimension lens** | Same pattern as the walkthrough's `user_query`: a lens, injected labeled into the prompt, never fabricated. |
| "if not, LLM sees all children and suggests groups, handled by CoT" | dimension **discovery step** inside the structured call: enumerate candidate dimensions in `reasoning`, pick one, output it as the `dimension` field | The discovery is CoT-shaped but lands in a schema field — the explanation is a first-class output, not something scraped from thinking. |
| "explanation of which feature was used, user can edit" | `dimension` is editable at gate 2 and **persisted** onto the run artifact and each group's `description` | Groups already have a `description` field (`GroupService.create`); the rationale becomes context every future prompt can read. |
| "2nd confirmation to edit or approve" | the **review gate**: new part state `awaiting_review`, proposal artifact doc, edit-carrying decision, server-side re-validation of edits | Designed as a harness seam (`ToolSpec.review`), implemented for the grouper first. |

## What already exists (and is used, not rebuilt)

| Existing | Role here |
|---|---|
| `GroupService` + `StructureGroupRepo` / `CodeElementGroupRepo` / `CallGroupRepo` (`api/v1/group_routes.py` is the human path) | The write path. The tool calls the same service the routes do — groups made by the tool are indistinguishable in kind from user-drawn ones (except origin tags, 05). |
| Three group kinds: `structure_group`, `code_element_group`, `call_group` — each holds one child kind | The **homogeneity law** the validator enforces: a proposal group never mixes kinds; mixed child lists get grouped per kind (02). |
| v2 harness: estimate gate, `interrupt()`, decision endpoint, patcher, tool registry | Gate 1 verbatim; gate 2 is a second interrupt through the same machinery (03). |
| agent-v3 shared: post-order n/a, but `written_commits` + run-level undo pattern (shared/03) | Undo semantics copied, and cheaper: one commit batch per approved run (05). |
| frontendv2: `tools/registry.ts` (`group`, coming-soon), the mock's ConfigForm steppers + done-face pills (frontendv2/03), faces registry | Frontend cost = flag flip + `wireId` + three face components; the review UI is the only genuinely new surface (04). |
| describe's descriptions | The grouping raw material: children are presented as `name (kind) — first sentence`. Undescribed children degrade quality → the gate-1 hint, same as document's (01). |

## Dendrogram

```
grouper
│
├── 01 tool spec           args & defaults · caps · refusal rules · estimate honesty
│                          · the two-gate run lifecycle
├── 02 prompt & context    child roster context · category lens vs CoT discovery
│                          · proposal schema · validator laws · one retry
├── 03 review gate         interrupt #2 · awaiting_review state · proposal doc on the
│                          mirror · edit-carrying decision · re-validation · the
│                          generic ToolSpec.review seam
├── 04 frontend            registry flips · ConfigForm (steppers + category) ·
│                          ReviewView (the editable proposal) · DoneView · badge
└── 05 write safety        write-on-approve · one commit batch · origin tags ·
                           human groups untouchable · regroup · undo
```

## Decisions (settled here)

1. **Read-only until approve.** The run's only side effects before gate 2 are
   artifact patches. Approve = the write; cancel = nothing to clean up.
2. **Scope: one parent's direct children, one run.** No subtree recursion in
   v1 — "group everything under src/ recursively" is a later loop the agent
   can drive tool-call by tool-call. Keeps the estimate exact and the review
   card humanly readable.
3. **Human-drawn groups are untouchable.** The tool only considers direct
   children *not already inside a group*. `regroup=true` additionally
   dissolves **agent-origin** groups (into the pool being regrouped); no flag
   reaches human ones. Same law as describe's overwrite (agent-v3 shared/03).
4. **The dimension is data.** `dimension` (one sentence, "grouped by pipeline
   stage") is a schema field: shown at gate 2, editable, stamped into each
   group's description and the run artifact. Never buried in reasoning.
5. **Ungrouped remainder is legal.** Forcing 14/14 children into groups
   produces "Misc". The model may leave items out with a reason; the
   validator bans a group named anything Misc-shaped; the review UI shows the
   remainder honestly.
6. **Gate 2 edits are re-validated server-side.** The user can rename, move,
   dissolve — but the same validator that judged the model judges the edit
   (counts, homogeneity, exactly-once). The frontend mirrors the rules for
   instant feedback; the backend's verdict is the real one.

## Build order

| Phase | Contents | Demo gate |
|---|---|---|
| **G1 — Proposal engine** | args + estimate + refusals · roster context · prompt + schema + validator + retry · tool returns the proposal (no writes, no gate 2 yet — auto-approve behind a flag) | fake-harness run over a 14-child node yields a valid proposal: dimension sentence, 2–6 homogeneous groups, every child accounted for |
| **G2 — Review gate** | second `interrupt()` · `awaiting_review` part state · proposal doc `group_proposal/<id>` on the mirror · decision endpoint accepts `{action, proposal}` · re-validation · write-on-approve via `GroupService` | approve in an HTTP test writes real groups in one commit batch; cancel writes nothing; an invalid edit is rejected with the validator's sentence |
| **G3 — Frontend** | `group` flag flip + `wireId` · ConfigForm (three steppers + category field) · `ReviewView` face (04) · DoneView pills · `awaiting review` badge | full flow in the panel: estimate → run → review card → move two children, rename a group, edit the dimension → approve → boxes on canvas |
| **G4 — Safety & polish** | origin tags · `regroup` · run-level undo (revert the batch) · evals (validator first-pass rate, % children grouped, dimension-edit rate) | undo returns the canvas to before; re-run with regroup restructures agent groups only; human-drawn group survives everything |
