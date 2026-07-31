# Frontend 01 — Overview and Structure

The frontend half of agent v2: turn the existing fixture-driven chat sidebar into
a real client of the conversation stream. Everything renders **typed parts** from
the backend's data model (data-model/01); the wire is the multi-doc patch protocol
(harness/02). Nothing in this plan interprets raw LLM output — same law as the
backend.

## What exists today (and its fate)

All under `src/frontend/src/features/Dashboard/features/Agent/`:

| Existing | Fate |
|---|---|
| `AgentSidebar` / `AgentOverlay` / `AgentToggleButton` / `AgentBottomBar` | **Panel chrome kept.** The sidebar's message list body is replaced by the real `ChatThread`. |
| `AgentChatInput` | Grows into the Composer (05): node chips, quick actions, stop button. |
| `types/conversation.ts` + `fixtures/conversations.ts` + `useConversationStore` | **Replaced** by wire types mirroring `app/agent/schemas/` and the mirror store (02). The fixture `event` part (ReplayRunner) is *not* part of the backend contract — cognitive replay stays a separate, client-side concern. |
| `walkthrough/` (TourOutline, StepPopover, executor, player, `useWalkthroughStore`, flatten/selectors) | **Untouched.** Mounted as the artifact renderer for `render: "walkthrough"` via a thin bridge (07). |
| `walkthrough/source/httpSource.ts` (NDJSON parsing) + `applyFrame.ts` (seq handling) | **Promoted**: the parsing/seq logic generalizes into the conversation stream source (02); the walkthrough-specific source stays until the old route is retired. |
| `walkthrough/components/Launcher.tsx` (node + depth select + estimate + start) | **Retired** in phase F3. Its job splits into: a quick action on the composer + the confirmation card (06). |
| chat/walkthrough `viewMode` toggle in the sidebar | Kept short-term; the walkthrough becomes an in-thread artifact, and the toggle becomes "expand artifact" (07). |

**Why keep the chrome and the player.** They already solve the hard UI problems
(canvas coexistence, popover layout, Monaco line mapping, playback state machine).
v2's frontend work is the *conversation surface*, not a redesign.

## Stack decisions (all already in the repo — zero new dependencies)

| Need | Use |
|---|---|
| collapsible thinking rows | `@radix-ui/react-collapsible` (`components/ui/collapsible.tsx`) |
| depth knob | `components/ui/slider.tsx` |
| verbosity knob | `components/ui/toggle-group.tsx` |
| progress bars | `components/ui/progress.tsx` |
| status chips | `components/ui/badge.tsx` |
| markdown in parts | `react-markdown` (already used by `StepMarkdown`) |
| patch application | `fast-json-patch` (already used by `applyFrame`) |
| store | zustand 5 + `devtools` + `useShallow` — the house pattern |
| toasts (fatal errors) | `sonner` |

## Target feature layout

```
features/Dashboard/features/Agent/
├── components/            (chrome — exists)
├── chat/
│   ├── ChatThread.tsx     message list, auto-scroll, virtualization seam
│   ├── Composer.tsx       input + chips + quick actions + stop      (05)
│   ├── parts/             one component per part type               (03, 04)
│   │   ├── TextPart.tsx · ReasoningPart.tsx · ToolPart.tsx · NodeRefChip.tsx
│   │   └── registry.ts    type → component
│   ├── tool/              ToolCard shell + ConfirmCard + ProgressRow (06)
│   └── artifacts/         render hint → component (walkthrough)      (07)
├── stream/
│   ├── types.ts           wire types (mirrors app/agent/schemas — hand-written, kept small)
│   ├── source.ts          fetch + NDJSON parse + frame dispatch
│   └── applyFrame.ts      multi-doc apply with `append` pre-pass
├── store/
│   ├── useMirrorStore.ts  docId → {snapshot, lastSeq, status}        (02)
│   └── useAgentRunStore.ts  active conversation, run status, pending decision
├── hooks/
│   ├── useRunStream.ts · useDecision.ts · useConversations.ts
└── walkthrough/           (exists, untouched; gains bridge.ts in 07)
```

## Build order (frontend phases, mapped to backend phases)

| Phase | Needs backend | Contents | Demo gate |
|---|---|---|---|
| **F1 — Stream skeleton** | Phase 1 (fake LLM) | wire types · mirror store · `useRunStream` · plain text parts in the existing sidebar; fixtures deleted | type a message, watch assistant text stream in and survive a reload |
| **F2 — Real parts** | Phase 2 | part registry · thinking UI (04) · effort knob (05) · markdown text parts · composer node chip from canvas selection | attach a node, ask a question — native thinking streams and collapses like Cursor, answer renders as markdown |
| **F3 — Tools** | Phase 3 | ToolCard states · ConfirmCard (depth slider with real max, verbosity) · walkthrough artifact bridge · Launcher retired | full flow: ask for a tour → confirm card → tour streams in-thread → play |
| **F4 — Polish** | Phase 4 | conversation list · usage footer from metadata · degraded ⚠ · cancel/stop UX · keyboard · error toasts | a 10-turn conversation feels like Cursor: smooth, honest, resumable |
