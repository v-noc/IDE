# Frontend v2 — 01: Structure, Conventions, Tokens

The folder must read like one person wrote it in one sitting. This doc fixes the
tree, the React rules, and the design tokens **before** any component is written —
every later doc assumes them.

## Target tree

```
features/Dashboard/features/AgentV2/
├── index.tsx                  entry: exports the overlay mount (same seam v1 uses)
│
├── panel/                     chrome — the 420px right panel
│   ├── AgentPanel.tsx         layout shell: header + thread + composer
│   ├── PanelHeader.tsx        status dot · "AGENT" · session id
│   └── PanelToggle.tsx        open/close affordance (behavior from v1, new skin)
│
├── thread/                    the conversation surface
│   ├── ChatThread.tsx         message list, auto-scroll, virtualization seam
│   ├── UserMessage.tsx        card: "YOU" label · node chips · text
│   ├── AgentMessage.tsx       plain row: "AGENT" label · markdown text
│   ├── parts/                 one component per wire part type
│   │   ├── registry.tsx       part type → component (exhaustive)
│   │   ├── TextPart.tsx       streaming markdown
│   │   ├── ReasoningPart.tsx  thinking row (spec: frontend/04 — unchanged)
│   │   └── NodeRefChip.tsx    attached-node pill (label + kind)
│   └── artifacts/             render hint → component
│       ├── registry.tsx
│       └── WalkthroughArtifact.tsx   bridge → existing player (frontend/07)
│
├── tool/                      the tool card (doc 03)
│   ├── ToolCard.tsx           shell: header row + badge + collapsible body
│   ├── ToolBadge.tsx          status pill (cva variants)
│   ├── ToolProgress.tsx       striped bar + "n / total unit · running…"
│   ├── faces/                 per-tool config + done faces
│   │   ├── registry.tsx       tool id → { icon, ConfigForm, DoneView }
│   │   └── walkthrough/       ConfigForm.tsx · DoneView.tsx · OutlineTree.tsx
│   └── controls/              shared form atoms
│       ├── DepthSlider.tsx    1..realMax · "n (this tree: max m)" label
│       ├── Segmented.tsx      Quick/Normal/Detailed control
│       └── Stepper.tsx        −/value/+ (group tool, when it ships)
│
├── composer/                  (doc 04)
│   ├── Composer.tsx           textarea + chip row + actions row
│   ├── NodeChip.tsx           attached node from canvas selection
│   ├── PickerMenu.tsx         shared Radix Popover shell (ToolPicker + EffortPicker)
│   ├── ToolPicker.tsx         popover menu over the tool registry
│   └── EffortPicker.tsx       "◇ medium" trigger → REASONING EFFORT dropdown (not EffortIndicator)
│
├── tools/
│   └── registry.ts            THE tool list: id, name, short, desc, icon, status
│
├── stream/                    ← moved from Agent/ unchanged (types, source,
│                                applyFrame + tests, seedArtifacts)
├── store/                     ← moved from Agent/ unchanged (useMirrorStore,
│                                useAgentRunStore, useConversationStore, selectors)
├── hooks/                     ← moved from Agent/ unchanged (useRunStream, useDecision)
│
├── walkthrough/               ← moved in V3; executor/store/source untouched,
│                                components/ restyled (doc 05)
│
└── theme/
    └── tokens.css             semantic CSS variables (this doc, below)
```

Out of scope, left in place: `Agent/engine/` + `useReplayStore` (cognitive
replay — plan/cognitive-replay owns their fate).

## React conventions (the "clean" in one page)

**Components**
- One component per file, named export matching the filename. No default exports
  except the feature `index.tsx`.
- A component is *presentation or wiring, never both*: components that read
  stores don't also lay out pixels — they select data and pass typed props down.
  Rule of thumb: anything in `parts/`, `faces/`, `controls/` takes props only.
- No component over ~150 lines; split by extraction, not by boolean props.

**Types**
- Wire types come from `stream/types.ts` only — no local redeclaration of part
  shapes. Part rendering switches on the discriminated union through the
  registry; add `never`-checked exhaustiveness so a new part type fails the build.
- Props interfaces live beside the component, exported only if a sibling needs them.

**State**
- Zustand with selectors + `useShallow` everywhere; never subscribe to a whole
  store from a leaf. Derive, don't duplicate: anything computable from parts
  (e.g. progress %) is computed in a selector, not stored.
- Local `useState` is allowed for *draft* UI state only (config-form edits before
  Run, textarea draft, menu open). The moment the backend learns about a value,
  it lives in the store.
- No `useEffect` for data derivation. Effects are for subscriptions and DOM.

**Styling**
- Tailwind utilities against the semantic tokens below. Zero raw hexes in TSX.
- Variant styling via `cva` (already in the repo): `ToolBadge`, buttons, the
  segmented control are cva components, not ternary-className soup.
- Animations honor `prefers-reduced-motion` (the striped bar, pulsing dots, and
  node glow all get static fallbacks).

**Accessibility**
- Everything clickable is a `<button>`. Collapsibles use Radix Collapsible
  (aria-expanded for free). Slider = Radix Slider; segmented = Radix ToggleGroup;
  picker = Radix Popover — all already in `components/ui/`.
- Focus is visible (ring token), Escape closes the picker, Enter sends /
  Shift+Enter newlines (04).

**Testing**
- Moved files keep their tests (`applyFrame.test.ts` etc.) — they must pass
  unmodified; that's the proof the move didn't fork the protocol.
- New pure logic gets vitest: tool-registry gating, config-form reducers
  (stepper cross-constraints), outline reshaping if any is added.
- No snapshot tests of styled markup — they rot with every design pass.

## Design tokens

Source: the mock's palette, verbatim. Scoped under the AgentV2 root class so the
rest of the app is untouched; expressed as semantic names so a light theme is a
value swap, not a refactor. Declared via Tailwind 4 `@theme` / CSS variables in
`theme/tokens.css`.

| Token | Value (from mock) | Used for |
|---|---|---|
| `--agent-bg-canvas` | `#0e0f11` (+ dot grid `#212329` / 22px) | canvas backdrop |
| `--agent-bg-panel` | `#141518` | panel |
| `--agent-bg-card` | `#191b1f` | user message, composer |
| `--agent-bg-tool` | `#1a1c21` | tool card, step card |
| `--agent-bg-inset` | `#15161a` | form fields, result boxes, segmented track |
| `--agent-bg-raised` | `#22252b` | chips, hover, progress track |
| `--agent-border` | `#22252b` / `#23262c` | default borders, dividers |
| `--agent-border-strong` | `#2c2f36` | buttons, chips, popover |
| `--agent-text` | `#e6e8ec` | primary text, titles |
| `--agent-text-body` | `#c3c8d1` | agent prose, step text |
| `--agent-text-muted` | `#8b919d` | meta, labels |
| `--agent-text-faint` | `#5c6270` / `#6b7280` | timestamps, section labels, hints |
| `--agent-accent` | `#3ecf72` | status dots, slider thumb, progress fill |
| `--agent-accent-text` | `#7fdba3` | icons, running/done badges |
| `--agent-accent-link` | `#61c98a` | links ("Open", stop links, "promote") |
| `--agent-accent-bg` | `rgba(62,207,114,.08–.12)` | icon tiles, chips, picker button |
| `--agent-accent-border` | `rgba(62,207,114,.2–.3)` | same, borders |
| `--agent-btn` / `--agent-btn-border` | `#2c9a58` / `#2f9d5c` (hover `#34ab63`) | primary buttons (Run, Next, Play, send) |
| `--agent-on-btn` | `#0b1a10` | text on primary buttons |
| `--agent-warn` | `#e2b95a` (+ `.09` bg / `.25` border tints) | "needs approval" badge, pending card border `#3a3320` |
| `--agent-danger` | *(not in mock — pick a quiet red in V4)* | error badge/face (03) |

**Typography.** Body: system stack (the mock uses it). Mono: `JetBrains Mono`
for ids, counters, meta lines, chips, section labels — add the font in V0, fall
back to `ui-monospace`. Key sizes from the mock: section labels 10–10.5px / 700 /
letter-spacing .08em; meta 10.5–11px mono; body 13.5px / 1.55–1.6; card title
13px / 600; step-card title 16px / 650.

**Radii.** Cards 12px · step card 14px · fields/buttons 8–9px · icon tiles 7px ·
pills 99px. Encode as three tokens: `--agent-r-card`, `--agent-r-field`,
`--agent-r-pill`.
