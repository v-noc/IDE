# Prompts 01 — The Prompt Registry

Every model-facing string in the system: named, versioned, layered, and
replaceable without touching harness code. This answers "improve the prompt — make
it easy to update and replace" structurally, not by writing one better prompt.

## The problem with the MVP's prompt layout

`app/walkthrough/prompts.py` is good (shared `PERSONA`/`GLOSSARY` constants,
per-call system templates) but has three growth problems:

1. the version lives far away (`PROMPT_VERSION` in `schemas.py`) and covers *all*
   prompts at once — you can't bump the intro prompt without lying about the
   block-plan prompt;
2. replacing a prompt for an experiment means editing source;
3. the agent, the walkthrough, and every future tool would each grow their own
   `prompts.py` with their own conventions.

## Decision: one registry, per-prompt versions

```python
# app/agent/prompts/registry.py

class PromptDef(BaseModel):
    name: str                        # "agent.system" · "walkthrough.intro_full" · …
    version: str                     # per PROMPT, not per module
    template: str                    # str.format slots: {persona} {glossary} {tools} …
    slots: list[str]                 # declared slots — render() rejects missing/extra

class PromptRegistry:
    def get(self, name) -> PromptDef
    def render(self, name, **slots) -> str      # fails loudly on slot mismatch
    def version(self, name) -> str              # stamped into metadata / artifacts
```

Prompt definitions live in small modules per domain (`prompts/agent.py`,
walkthrough's migrate in place), registered at import. Shared building blocks —
`PERSONA`, `GLOSSARY` — are slots filled from **one** constant, so the agent and
every tool cite the same glossary and a wording fix lands everywhere at once.

**Why declared slots.** A template that silently ignores a typo'd slot ships a
broken prompt to production with no error. Failing at render time (and a unit test
that renders every registered prompt with dummy slots) turns prompt typos into CI
failures.

**Why per-prompt versions.** Versions exist for evals: "intro quality dropped —
what changed?" needs `walkthrough.intro_full@5`, not "the module changed". Each
assistant message stamps `agent.system`'s version in its metadata; each artifact
stamps the versions of the prompts its tool used.

## Replacement without code edits

```
settings.PROMPT_OVERRIDE_DIR (optional, dev-only)
  prompts/overrides/agent.system.md          ← plain file, front-matter: version
```

At boot, files in the override dir shadow registered templates (same declared
slots enforced). **Why:** prompt iteration is the highest-frequency edit in an LLM
product; a file swap + restart beats a code change + review for experiments, while
production still runs the in-repo, code-reviewed registry (the override dir is
empty there). The stamped version always tells the truth about what ran.

## The orchestrator system prompt — layered

```
layer 1  identity + hard rules                      (static)
         · you coordinate tools over a code graph; you never author tour
           content, descriptions, or docs yourself — tools do
         · only use node ids from the user's attached nodes or prior tool
           results in this conversation; if you have none, ask — never guess
         · before each tool call, say in ONE short plain sentence what you'll
           do next and why ("I'll tour charge at depth 1 — it's small") —
           no ids, no schema talk. Never narrate your reasoning; if you have
           a thinking channel, think there (harness/04)
         · the harness shows the user every task tool's cost; relay estimates
           honestly; when over cap, suggest a smaller depth
layer 2  <project name=…>description</project>      (dynamic slot, every turn — context/03)
         + domain glossary                          (shared constant)
layer 3  tool inventory                             (generated from ToolSpec descriptions)
layer 4  behavioral defaults                        (static)
         · exactly one attached node + clear intent → act, no clarifying question
         · attached nodes arrive with their <attached_node> block — answer from
           it directly; a plain question needs no tool
         · walkthrough asks: distill user_query / verbosity / suggested depth
           per the distillation rules (context/03)
         · after a task: one-line outcome + degraded count; never re-narrate
           the artifact
```

**Why layers.** Static layers cache (prompt-caching boundary friendly) and diff
cleanly; the only per-turn variance is the project slot and the generated tool
inventory. Layer 3 being *generated* means a new tool updates the prompt by
existing — no prose to forget.

## Eval hooks

- every registered prompt renders in CI (slot check + token-budget assertion for
  the worst-case project header);
- orchestrator evals are scripted turns asserting **tool choice and args** (which
  tool, which node id, which depth/verbosity) — greppable, unlike prose;
- bump a version → re-run that prompt's fixtures; the stamped versions in
  metadata/artifacts make regressions attributable.
