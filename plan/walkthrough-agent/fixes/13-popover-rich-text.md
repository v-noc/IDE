# 13 — Rich-text popover: markdown + code highlighting, scrollable, expandable to a dialog

## What this builds

The step popover (and the node-anchored popover from fix 07/10) currently renders
`step.text` as one plain `<p>`. Wanted:

1. **Rich text** — markdown rendering with a syntax-highlighted code renderer, so
   narration can contain `inline_identifiers` and fenced snippets.
2. **Bounded height** — the popover never grows past a cap; overflow scrolls.
3. **Expand** — a maximize button turns the step into a **dialog** with bigger
   width and the same rendering — the same affordance the canvas code view already
   has (`NodeCodeView`'s Maximize2 button → `CodeViewDialog.tsx`; read that file
   and mirror its pattern).

## Dependencies (verify before adding)

- `grep -rn "react-markdown" src/frontend/src src/frontend/package.json` — if absent
  (expected): `yarn add react-markdown remark-gfm`. These are the only new packages.
- **Do NOT add a highlighter.** `@shikijs/core` is already a dependency (BlockNote's
  code block uses it). Find the existing usage first:
  `grep -rn "@shikijs\|createHighlighter\|codeToHtml" src/frontend/src` — if the
  Docs feature already builds a highlighter instance, reuse its module; only if
  nothing exists, create the singleton described below.
- Radix Dialog is installed (`@radix-ui/react-dialog`) and the project has a
  `components/ui` wrapper — use the existing `Dialog` ui component, same as
  `CodeViewDialog` does.

## Files

| File | Action |
|---|---|
| `walkthrough/components/StepMarkdown.tsx` | NEW — the shared renderer (markdown + shiki code) |
| `walkthrough/components/useShikiHighlighter.ts` | NEW (only if no existing shiki singleton) |
| `walkthrough/components/StepPopover.tsx` | Body uses StepMarkdown; max-height + scroll; ⤢ expand button |
| `walkthrough/components/StepDialog.tsx` | NEW — the expanded view |
| `walkthrough/store/useWalkthroughStore.ts` | `stepDialogOpen: boolean` + `setStepDialogOpen` |
| `walkthrough/hooks/useWalkthroughKeyboard.ts` | Escape must close the dialog, not exit the tour |
| `src/backend/app/agent/llm/fake.py` | Emit markdown-ish sample text so mock mode exercises the renderer |

## Piece 1 — `StepMarkdown`

```tsx
export function StepMarkdown({ text }: { text: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      skipHtml                 // narration is LLM output; never render raw HTML
      components={{
        a: (props) => <a {...props} target="_blank" rel="noreferrer" className="underline" />,
        code: CodeRenderer,    // below
        // p / ul / ol / li: small spacing classes; keep text-sm leading-relaxed
      }}
    >
      {text}
    </ReactMarkdown>
  );
}
```

Rules:

- `skipHtml` stays on — this is a security boundary, not a style choice.
- No tailwind-typography plugin exists in this project; style the handful of
  elements explicitly (p, lists, code, pre, a, strong). Keep it minimal — narration
  is short prose, not documents.
- `CodeRenderer`: inline code (`inline` prop true) → styled `<code>` (muted bg,
  rounded, mono, text-[0.85em]). Fenced blocks → shiki-highlighted `<pre>` via the
  singleton; **while the highlighter loads, render a plain `<pre>` immediately**
  (no empty flash), swap when ready.

**Shiki singleton** (skip if the Docs feature already exposes one):

- One module-level promise, created on first use — never per component:
  `createHighlighterCore` from `@shikijs/core` with a **small fixed set**: langs
  `python, typescript, javascript, json, bash`, themes `github-light`,
  `github-dark` (fine-grained imports from `shiki/langs/...` / `shiki/themes/...`
  per shiki v3 docs — verify import paths against the installed version in
  `node_modules/@shikijs/core/package.json`).
- Theme picked from `next-themes` `resolvedTheme` (same switch `NodeCodeView` uses
  for Monaco).
- Unknown language on a fence → plain `<pre>`, no error.
- The hook returns `html | null`; render with `dangerouslySetInnerHTML` **only** for
  shiki output (shiki escapes its input — that is safe; raw markdown HTML stays
  skipped).

## Piece 2 — popover body: cap + scroll

In `StepPopover.tsx`:

```tsx
<div
  className="max-h-60 overflow-y-auto overscroll-contain pr-1 text-sm leading-relaxed"
  onWheel={(e) => e.stopPropagation()}   // scroll the text, never zoom the canvas
>
  {waitingForText ? <GeneratingShimmer /> : <StepMarkdown text={step.text} />}
</div>
```

- `max-h-60` (240 px) is the cap; tune visually, keep it a class.
- `stopPropagation` on wheel does not prevent local scrolling — it only stops the
  canvas zoom behind it (fix 07 already requires this on the popover root; keep
  both, they are cheap).
- Header row gains the expand button next to the ⚠/counter:
  `<Maximize2 className="h-3.5 w-3.5" />`, `onClick={() => setStepDialogOpen(true)}`
  with `stopPropagation` — mirror the button styling from `NodeCodeView`'s expand.

## Piece 3 — `StepDialog`

State lives in the **store**, not the popover (`stepDialogOpen`) — the popover
unmounts/moves between steps, and the dialog must survive Next/Prev while open.

- Radix `Dialog` via the project's ui wrapper, `open={stepDialogOpen}`,
  `onOpenChange={setStepDialogOpen}`.
- Content: `max-w-3xl w-[min(90vw,48rem)]`; header = step title + counter + ⚠;
  body = `<StepMarkdown text={step.text} />` in `max-h-[70vh] overflow-y-auto`;
  footer = Exit · Prev · Next (reuse the same store actions — the dialog is just a
  bigger view of the CURRENT step; on Next, its content swaps in place).
- It subscribes to `playerSteps[cursor]` itself; renders nothing when
  `phase !== "playing"` (and force-closes via an `onOpenChange` guard when the tour
  exits — verify `exit()` also sets `stepDialogOpen = false` in the store; add that
  to `exit()` and `discard()`).
- Mount it once in `WalkthroughStepOverlay` next to the pill and executor.
- Canvas actions still run on step change while the dialog is open (the canvas
  animates behind the Radix overlay). Accept this; do not add suppression logic.

## Piece 4 — keyboard interplay

`useWalkthroughKeyboard`:

- When `stepDialogOpen` is true, **do not handle Escape** (return early for that
  key) — Radix closes the dialog on Escape; today the hook would also `exit()` the
  whole tour on the same keypress. One `if (event.key === "Escape" && stepDialogOpen) return;`
  before the existing Escape branch.
- Arrow keys keep working while the dialog is open (focus is inside the dialog;
  targets are buttons, not inputs — the existing input/textarea guard already
  allows this; verify by testing, not assuming).

## Piece 5 — make the mock exercise it (backend, ties into fix 11)

In `agent/llm/fake.py`, make the fake texts markdown-flavored so the renderer is
visibly working in mock mode:

- Intro: include the node name as inline code — ``This `charge` function …``.
- One block text per code stop includes a short fenced snippet:
  ```
  f"The block starts by validating input:\n\n```python\nif not card.valid():\n    raise PaymentError()\n```\n\nThen it proceeds."
  ```
- Keep other texts plain — the popover must look right for BOTH plain and rich text.

Also add one line to the parent plan's prompt rules when the real LLM lands
(`../07-prompting.md` layer-3 output rules): narration may use markdown **inline
code and fenced blocks only** — no headings, no images, no links unless asked. Do
not change the prompts now; just leave the marker so the rule isn't forgotten.

## Prove it

1. Mock tour: intro shows the node name as inline code; one block shows a
   highlighted python snippet (correct colors in both light and dark theme).
2. A long text (force one in the fake ≥ 800 chars) scrolls inside the popover;
   wheel-scrolling the text never zooms the canvas; the popover height never
   exceeds the cap.
3. ⤢ opens the dialog: wide, same content richly rendered; Next/Prev inside the
   dialog walk the tour with the canvas animating behind the overlay; the popover
   and dialog never show different steps.
4. Escape with the dialog open closes only the dialog; second Escape exits the
   tour. Exit while the dialog is open closes both.
5. No highlighter flash: fenced code appears instantly as plain `<pre>` and
   upgrades to highlighted without layout jump (same font/size for both states).
6. `yarn lint` + `yarn test` green; bundle check: `yarn build` and confirm shiki
   langs are the small fixed set, not the full grammar pack (build output size
   sanity vs before).
