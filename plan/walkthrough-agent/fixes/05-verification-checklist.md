# 05 — Verification checklist (run after fixes 01–04)

Run everything. Check boxes only for things you actually saw happen.

## Automated

```
cd src/backend  && uv run pytest tests/unit/walkthrough -q      # expect: 0 failed
cd src/backend  && uv run python -c "import app.api.root; print('ok')"
cd src/frontend && yarn test                                     # expect: 0 failed
cd src/frontend && yarn lint
```

- [ ] All four commands green (paste outputs into the PR/notes).
- [ ] The 3 previously-failing backend tests now pass **unmodified** (except the
      over-cap fixture rewrite explicitly allowed in 04-B2).

## Manual — mock demo on a real project (the user's core complaint)

Open a real project in the app (mock mode on).

1. **Real data**
   - [ ] Select a class with methods → Estimate → node count matches what the canvas
         shows at that depth.
   - [ ] Generate → outline rows show the REAL names of the class and its methods.
   - [ ] Play → canvas pans to each real node; Monaco opens the node's real code;
         highlighted ranges sit inside that function's actual lines; popup text is
         lorem.
   - [ ] A function under 8 lines gets exactly one block (whole body).
   - [ ] Each gated function got 2–5 contiguous blocks covering its range.
2. **Calls and duplicates**
   - [ ] A call stop opens code (the target's body) and highlights inside it (F3 +
         B5 both matter here).
   - [ ] A second call to the same target appears as a contextual stop (link, no
         code phase).
3. **Play flow (fix 02)**
   - [ ] "▶ Play walkthrough" is visible in the panel while the outline is still
         filling; card appears only after Play.
   - [ ] Card ≈ 440 px, centered, clear of the Sandbox bar.
   - [ ] Next to step 3 → Esc → view restored → Resume → back at step 3.
   - [ ] Outrun generation with Next → shimmer → auto-advance on arrival.
   - [ ] Stay playing until generation completes → card does NOT vanish (F2).
4. **Edges**
   - [ ] Start a tour from the project root node — no error (F1).
   - [ ] Generate over an existing finished tour → confirm dialog (F7).
   - [ ] Pan by hand mid-step → no re-centering until the next step; tour's own pans
         don't disable following steps' pans (F6).
   - [ ] Exit always restores selection/expansion/focus.

## Manual — backend smoke (fake provider, real backend)

With the backend running and `VITE_WALKTHROUGH_MOCK=0`,
`WALKTHROUGH_LLM_PROVIDER=fake`:

- [ ] `curl -N -X POST .../api/v1/walkthroughs/run -d '{"project_id":"...","node_id":"...","depth":1}' -H 'content-type: application/json'`
      → hello frame first, monotonic `seq`, terminal `end` frame.
- [ ] Second POST while one runs → 409 with the active session id.
- [ ] `WALKTHROUGH_LLM_PROVIDER=openai` (no key) → single `end/error` frame,
      message names the provider (B8) — not a degraded lorem tour.
- [ ] Frontend against this backend: same UI behavior as mock mode.

## Sign-off

- [ ] Parking-lot items from `fixes/README.md` copied into an issue/note, not left
      in code comments.
- [ ] `git status` shows only intended files; commit fixes separately from any new
      features, message references this folder.
