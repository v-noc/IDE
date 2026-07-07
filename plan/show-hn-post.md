# Show HN draft

> Save this as the body when you submit. The title field on HN is short (≤ 80 chars).
> Use one of the title options below; pick whichever feels least salesy on the day.

---

## Title options

Pick one. They're ordered from "most direct / least clickbaity" to "most opinionated".

1. **Show HN: V-NOC — a graph-based IDE where the codebase is the database**
2. **Show HN: V-NOC – an IDE that replaces the file tree with a logic graph**
3. **Show HN: V-NOC — stop reading files, read the call graph**
4. **Show HN: A graph IDE on top of TerminusDB (logs, tests, version history as edges)**

My pick: **#1**. It's accurate, fits in the character budget, and doesn't promise anything the demo can't show.

---

## Body

> Hi HN — I've been building V-NOC for about a year. It's a coding environment that replaces the file tree with a **logic graph**: functions, classes, files, and folders are nodes; calls, imports, and dependencies are edges. Logs, tests, playgrounds, documents, and version history all attach to the same nodes, so context comes to the symbol instead of you grepping for it.

**Live demo (no signup):** https://vnoc.vercel.app/project/claudecode

The demo is Anthropic's open-source Claude Code repo, parsed and rendered as a graph. You can pan around, expand nodes, follow call edges, and open the logs/tests/docs panels.

**Focus mode** is the part I most want feedback on. Any function or class can be isolated and shared via URL — you get just that symbol plus the neighbours it actually depends on, nothing else. Example, focusing on a single function from the same project:

https://vnoc.vercel.app/project/claudecode?focus=FunctionSchema%2Fbc5f3f55-c4a7-479c-adc5-982a607e20b9

That's the link a teammate would paste in a code review instead of "see `src/foo/bar.py:412`". Open it in a new tab — the whole rest of the codebase disappears and you're left with the function, its callers, its callees, and the MRO chain it sits in.

### Why I built it

Files aren't real structures; they're storage. The mental model that makes a codebase navigable lives in your head, and it grows faster than the code. We've all worked on systems where a 5-line change costs a day because you have to rebuild that mental model first. That cost compounds — and it's what most of the "junior vs senior" gap actually measures.

Graph databases already solved navigation for the rest of the world (knowledge graphs, social networks). It seemed strange that source code, which **is** a graph, is still presented as a tree of buckets. So I built the obvious thing.

### How it works (1-minute version)

- **Backend** — FastAPI (REST + JSON-RPC) over **TerminusDB**, a graph DB with built-in Git-style version control. Branches, commits, diffs, push/pull are TerminusDB primitives, so versioning the *graph* (not just the text) comes for free.
- **Language drivers** — small JSON-RPC services that turn source into language-agnostic AST nodes. Python uses Jedi + LibCST; TS/JS uses ts-morph on Bun. Adding a language = adding a driver, not editing the backend.
- **Stable symbol IDs** — the parser injects a UUID into each function/class as a docstring/comment (e.g. `""" ID: 7b1d… """`). The ID survives renames, moves, and reformats. That's how logs, tests, playgrounds, and shared focus URLs stay glued to the right symbol.
- **Logs** — a tiny `vn-logger` Python decorator emits structured events tagged with the function ID, parent ID, and chain ID. The result is an execution tree on the canvas, not a tail of flat lines.
- **Tests** — discovered via the same parser, linked to the symbols they cover by static analysis + runtime tracing. "What's covered?" becomes a graph query.
- **Agents** — work on a fresh TerminusDB branch. You review the symbol-level diff before merging. No 100-message chat to trust.

### What it isn't (yet)

- Not a full code editor. Editing happens in your editor; V-NOC is the navigation/observation layer. Bidirectional sync is via a filesystem watcher.
- Python and TS/JS only. Other languages show up as opaque file nodes.
- Performance: parsing a very large repo for the first time is slow. The call-chain resolver is the main bottleneck and is on the list to rewrite in Rust.
- The hosted demo is read-only against a snapshot — local install gives you the editing + agent flows.

### Run it locally

Apache-2.0. The repo has a `make help` that lays out every entry point, and a `doc/` folder organised top-down (vision → architecture → getting started → creating a project → drivers → tracking → logs → playground → tests → version control).

```
git clone <repo>
make install && make install-lsp
make start-db   # TerminusDB on :6363
make dev        # backend :8000, JSON-RPC :8050, frontend :5173
```

### What I'd love feedback on

1. The **focus URL** as the primitive for sharing code context. Does it feel useful, or just a clever party trick?
2. The **graph-as-database** thesis. Is there a class of bug or workflow where it would genuinely change the game for you, or is the file tree just fine?
3. **TerminusDB for versioning the graph itself** (not the source text). I think it's the right call but it's an unusual dependency — curious if anyone has lived experience to share.
4. Performance horror stories from your own large codebases — what would I have to handle to make this work for you?

Happy to answer anything. Discord is in the repo if you'd rather chat there.

---

## Submission checklist

- [ ] Re-check the demo is up and the focus link still resolves
- [ ] Make sure the repo README is the polished version (links to `doc/` work)
- [ ] Post early-morning US Pacific (best HN traffic window)
- [ ] Be in the thread for the first 2 hours — answer every comment
- [ ] Don't argue with critics; concede honestly, take notes
- [ ] If it gets traction, capture the feedback themes into `plan/` for follow-up

## Things to have ready in case of front-page

- A short Loom of focus mode in action (60s, no audio is fine)
- A clean `git log` of the last month so people can see it's actively built
- An issue template for "I tried it on my repo and X broke"
- Sample TerminusDB queries (people will ask "show me the graph")
- A direct DM channel (Discord invite is already in the README)

## Things NOT to do

- Don't lead with "AI-native". HN allergy.
- Don't make grandiose claims about replacing IDEs.
- Don't dunk on "files and folders" in the title — keep that for the body.
- Don't post and run. The post lives or dies in the first comment thread.
