# Frontend v2 — 06: Build Order and v1 Retirement

Five phases; each ends runnable and demoable. The old `Agent/` folder keeps
working until V4 — at no point is the app without a functioning agent panel.

## The dev switch (historical)

V0–V3 originally used a `VITE_AGENT_V2` flag to mount the new panel beside v1.
**Done:** the new presentation lives in `Agent/` in place; no dev switch remains.

## V0 — Scaffold ✓

1. `Agent/` tree (01): `index.tsx`, `panel/`, `theme/tokens.css`.
2. Tokens + JetBrains Mono wired; panel renders themed.
3. Lint clean under the repo eslint config; no `any`, no raw hexes.

**Gate:** themed empty panel beside the canvas.

## V1 — Thread ✓

1. `stream/`, `store/`, `hooks/` kept in `Agent/`; presentation rebuilt in `thread/`, `composer/`.
2. `ChatThread`, `UserMessage`, `AgentMessage`/`TextPart`, `NodeRefChip` (02).
3. Minimal composer: textarea + send + node chip from canvas selection.
4. Auto-scroll rules; reload restores the conversation.
5. `ReasoningPart` restyle.

**Gate:** attach a node, ask a question — enriched answer streams in the new skin.

## V2 — Tool card ✓

1. `ToolCard` shell + `ToolBadge` + expansion defaults (03).
2. Face registry + generic fallback face + `ToolProgress`.
3. Walkthrough `ConfigForm` + `useDecision` approve/reject.
4. Walkthrough `DoneView`: play button + outline tree + footer.
5. Artifact bridge via `useWalkthroughBridge`.
6. Error + cancelled faces.

**Gate:** full walkthrough flow in the new skin.

## V3 — Picker, effort, playback skin ✓

1. `tools/registry.ts` + gating helper + tests (04).
2. `ToolPicker` with coming-soon rows.
3. `toolHint` on send (backend + frontend wired).
4. `PickerMenu` → `EffortPicker` + send/Stop swap.
5. Reskin step popover, pill, node highlight, `StepDialog` (05).

**Gate:** picker shows four tools, one usable; overlays match the mock.

## V4 — Polish and retirement ✓

1. Danger token + a11y on collapsibles; reduced-motion in tokens.
2. Panel-header status dot; session id.
3. Delete v1 presentation cruft (see checklist).
4. `WorkspaceLayout` imports `Agent` directly (no switch).
5. `yarn test`, `yarn build` pass.

**Gate:** one `Agent/` feature folder; no v1 presentation files remain.

## Retirement checklist (V4 step 3, explicit)

- [x] `Agent/chat/**` deleted (replaced by `thread/` + `tool/` + `composer/`)
- [x] `Agent/components/**` deleted (replaced by `panel/`)
- [ ] `Agent/types/conversation.ts` — kept for `engine/` + replay path
- [x] `Agent/walkthrough/components/` legacy panel UI deleted; executor/store kept
- [x] `Agent/stream|store|hooks` in place (not moved to a second folder)
- [ ] `Agent/engine/**` + `useReplayStore` — kept until cognitive-replay plan lands
- [x] dev switch removed from `WorkspaceLayout`
- [x] `useAgentOverlayStore` serves panel chrome

## Risks, named

| Risk | Mitigation |
|---|---|
| Two skins drift while both exist | stores shared from V1; v1 gets no new features after V0 |
| `toolHint` lands frontend-first and rots | it's a V3 gate item with the backend; don't merge half |
| Restyle quietly breaks executor math | walkthrough logic moves untouched with its tests; only `components/` files are edited |
| Token file becomes a second design system | tokens map 1:1 to the mock palette; new colors require a mock update first |
