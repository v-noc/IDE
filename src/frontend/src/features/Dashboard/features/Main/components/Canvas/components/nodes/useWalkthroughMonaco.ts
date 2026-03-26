import { useCallback, useEffect, useRef, useState } from "react";
import type { editor } from "monaco-editor";
import type { Monaco, OnMount } from "@monaco-editor/react";

import { useWalkthroughStore } from "@/features/Dashboard/features/Agent/walkthrough/store/useWalkthroughStore";

/**
 * Walkthrough line highlights (Monaco decorations) + in-editor spotlight and
 * a `data-walkthrough-code-anchor` node so PopoverLayer can anchor to a line.
 * Mirrors Monaco tour patterns: getTopForLineNumber, scrollTop, getLayoutInfo content box.
 */
export function useWalkthroughMonaco(
  nodeId: string | undefined,
  showDiff: boolean,
): { onMount: OnMount } {
  const [editor, setEditor] = useState<editor.IStandaloneCodeEditor | null>(
    null,
  );
  const monacoRef = useRef<Monaco | null>(null);
  const decoIdsRef = useRef<string[]>([]);

  const highlightsEntry = useWalkthroughStore((s) =>
    nodeId ? s.highlights.get(nodeId) : undefined,
  );
  const popoverVisible = useWalkthroughStore((s) => s.popoverVisible);
  const popover = useWalkthroughStore((s) => s.popover);

  const onMount: OnMount = useCallback((ed, m) => {
    monacoRef.current = m;
    setEditor(ed);
  }, []);

  useEffect(() => {
    if (!editor || showDiff || !monacoRef.current) return;
    const m = monacoRef.current;
    const model = editor.getModel();
    if (!model) {
      decoIdsRef.current = editor.deltaDecorations(decoIdsRef.current, []);
      return;
    }

    const lines = highlightsEntry?.lines;
    const decos =
      lines?.flatMap((range) => {
        const lc = model.getLineCount();
        const from = Math.max(1, Math.min(range.from, lc));
        const to = Math.max(from, Math.min(range.to, lc));
        return {
          range: new m.Range(from, 1, to, model.getLineMaxColumn(to)),
          options: {
            isWholeLine: true,
            className: "walkthrough-monaco-line-deco",
          },
        };
      }) ?? [];

    decoIdsRef.current = editor.deltaDecorations(decoIdsRef.current, decos);
    return () => {
      decoIdsRef.current = editor.deltaDecorations(decoIdsRef.current, []);
    };
  }, [editor, showDiff, highlightsEntry]);

  useEffect(() => {
    if (!editor || showDiff || !highlightsEntry?.lines?.length) return;
    const start = Math.min(...highlightsEntry.lines.map((l) => l.from));
    const model = editor.getModel();
    const lc = model?.getLineCount() ?? 0;
    if (start >= 1 && start <= lc) {
      editor.revealLineInCenter(start);
    }
  }, [editor, showDiff, highlightsEntry]);

  useEffect(() => {
    if (!editor || showDiff || !nodeId) return;
    const root = editor.getDomNode();
    if (!root) return;

    const spotlight = document.createElement("div");
    spotlight.className = "walkthrough-monaco-spotlight";
    spotlight.setAttribute("aria-hidden", "true");

    const anchorEl = document.createElement("div");
    anchorEl.setAttribute("data-walkthrough-code-anchor", "");
    anchorEl.setAttribute("data-node-id", nodeId);

    root.appendChild(spotlight);
    root.appendChild(anchorEl);

    let bumpRaf = 0;
    const bumpLayout = () => {
      if (bumpRaf) return;
      bumpRaf = requestAnimationFrame(() => {
        bumpRaf = 0;
        const st = useWalkthroughStore.getState();
        const pa = st.popover?.anchor;
        if (
          st.popoverVisible &&
          pa?.type === "code-line" &&
          pa.nodeId === nodeId
        ) {
          st.bumpCodeAnchorLayoutEpoch();
        }
      });
    };

    const sync = () => {
      const layout = editor.getLayoutInfo();
      const model = editor.getModel();
      const lc = model?.getLineCount() ?? 0;

      const hl = highlightsEntry?.lines;
      if (hl?.length && lc > 0) {
        const start = Math.max(1, Math.min(Math.min(...hl.map((l) => l.from)), lc));
        const end = Math.max(start, Math.min(Math.max(...hl.map((l) => l.to)), lc));
        const top = editor.getTopForLineNumber(start) - editor.getScrollTop();
        const bottom =
          editor.getTopForLineNumber(end + 1) - editor.getScrollTop();
        const height = Math.max(1, bottom - top);
        spotlight.style.display = "block";
        spotlight.style.top = `${top}px`;
        spotlight.style.height = `${height}px`;
        spotlight.style.left = `${layout.contentLeft}px`;
        spotlight.style.width = `${layout.contentWidth}px`;
      } else {
        spotlight.style.display = "none";
      }

      const pa = popover?.anchor;
      if (
        popoverVisible &&
        pa?.type === "code-line" &&
        pa.nodeId === nodeId &&
        lc > 0
      ) {
        const ln = Math.max(1, Math.min(pa.line, lc));
        const top = editor.getTopForLineNumber(ln) - editor.getScrollTop();
        const bottom = editor.getTopForLineNumber(ln + 1) - editor.getScrollTop();
        const height = Math.max(1, bottom - top);
        anchorEl.style.display = "block";
        anchorEl.style.position = "absolute";
        anchorEl.style.pointerEvents = "none";
        anchorEl.style.top = `${top}px`;
        anchorEl.style.height = `${height}px`;
        anchorEl.style.left = `${layout.contentLeft}px`;
        anchorEl.style.width = `${layout.contentWidth}px`;
        anchorEl.setAttribute("data-line", String(pa.line));
      } else {
        anchorEl.style.display = "none";
      }

      bumpLayout();
    };

    const d1 = editor.onDidScrollChange(sync);
    const d2 = editor.onDidLayoutChange(sync);
    sync();

    return () => {
      if (bumpRaf) cancelAnimationFrame(bumpRaf);
      d1.dispose();
      d2.dispose();
      spotlight.remove();
      anchorEl.remove();
    };
  }, [
    editor,
    showDiff,
    nodeId,
    highlightsEntry,
    popover,
    popoverVisible,
  ]);

  return { onMount };
}
