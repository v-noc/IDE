# 04 — Persistence

How sessions land in TerminusDB, what "pinned to a commit" means concretely, and the
replay read path.

## The document type

A new doc type in `app/db/schema/` beside the existing ones:

```
WalkthroughSessionSchema
├── id, created_at
├── project_id
├── request        {node_id, depth}
├── branch         str          ← captured at run start
├── commit_id      str          ← TerminusDB head commit at run start
├── visit_list     json         ← the full VisitList (stops, order, modes)
├── node_steps     list[json]   ← appended per node_done
├── status         enum: generating | complete | error | aborted
├── error_log      list[str]
├── schema_version str
├── prompt_version str
├── model_id       str          ← "provider:model" (02)
└── usage          {prompt_tokens, completion_tokens}
```

`visit_list` and `node_steps` are stored as opaque JSON blobs, not as graph-linked
documents. Deliberate: sessions are **records**, not graph data — nothing queries
"which sessions touch node X" in MVP, and blob storage means schema evolution is a
`schema_version` bump, not a TerminusDB migration.

## Write path (incremental, truthful)

| Moment | Write |
|---|---|
| Run start | Create doc: request, branch, commit_id, visit_list, `status=generating` |
| Each `node_done` | Append that `NodeSteps` to `node_steps` (one small update; ~1/stop) |
| End | `status=complete` + usage. Error/abort paths set their status the same way |

A crash at any point leaves a document that says exactly what happened and holds every
finished stop — that is what makes later resume-from-`seq` a pure read problem.

The patcher's mirror (03) **is** the document: `persistence.py` serializes the same
object the frames describe. One truth, two consumers (wire, DB).

## Commit pinning — what it means concretely

TerminusDB versions the whole graph with git-style commits (branches, commit ids,
time-travel reads). The session captures `branch` + `commit_id` **once, at run start,
before traversal**, and then:

- **During generation**: traversal and `context.py` read node data and code *at that
  commit* (ref-scoped reads), so a parser re-index landing mid-run cannot shift line
  numbers under the block planner.
- **On replay**: `GET /walkthroughs/{id}` returns the session; the frontend asks the
  existing node/code endpoints for data at `commit_id`. Highlights match the recorded
  line numbers forever, regardless of what happened to the code since.

MVP boundary, stated honestly: if the existing code/read endpoints can't take a ref
parameter yet, generation still captures the pin (writes are cheap and correct now),
and replay-at-commit becomes the follow-up that threads a `ref` through those reads.
The frontend already degrades visibly on drift (frontend 05, #13). **Do not skip the
capture** — it costs two fields and unlocks the whole feature later.

## Replay read path

```
GET /walkthroughs/{session_id}
  → session doc (as-is)

frontend loads it (frontend 02: same mirror, no stream)
  → node/code fetches at session.commit_id (or today's head, degraded, until
    ref-scoped reads land)
```

No listing endpoint in MVP (the session-library UI is deferred, parent 02); the id
comes from the `hello` frame the client kept, or from the dev CLI output.

## Retention

Nothing automatic in MVP. Sessions are small (tens of KB — text, ranges, ids; never
code bodies). If dogfooding produces clutter, a `DELETE /walkthroughs/{id}` is ten
lines. Not built until needed.
