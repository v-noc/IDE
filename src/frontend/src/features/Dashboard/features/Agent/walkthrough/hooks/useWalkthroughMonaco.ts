import { useCallback, useEffect, useRef, useState } from "react";
import type { Monaco } from "@monaco-editor/react";
import type { editor } from "monaco-editor";
import { useWalkthroughStore } from "../store/useWalkthroughStore";
import { currentStepAnchor } from "../store/selectors";
import {
  absoluteToEditorLine,
  clampEditorRange,
} from "../executor/lineMapping";

export function useWalkthroughMonaco(
  nodeId: string,
  nodeStartLine: number | undefined,
  showDiff: boolean,
  codeLoaded: boolean,
) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<Monaco | null>(null);
  const decorationIdsRef = useRef<string[]>([]);
  const syncCleanupRef = useRef<(() => void) | null>(null);
  const bumpRafRef = useRef<number | null>(null);
  const [editorMounted, setEditorMounted] = useState(0);

  const phase = useWalkthroughStore((s) => s.phase);
  const highlight = useWalkthroughStore((s) =>
    s.highlight?.nodeId === nodeId ? s.highlight : null,
  );
  const cursor = useWalkthroughStore((s) => s.cursor);
  const bumpAnchorEpoch = useWalkthroughStore((s) => s.bumpAnchorEpoch);

  const scheduleBump = useCallback(() => {
    const anchor = currentStepAnchor(useWalkthroughStore.getState());
    if (anchor?.type !== "code-line" || anchor.nodeId !== nodeId) return;
    if (bumpRafRef.current != null) return;
    bumpRafRef.current = requestAnimationFrame(() => {
      bumpRafRef.current = null;
      bumpAnchorEpoch();
    });
  }, [nodeId, bumpAnchorEpoch]);

  const onMount = useCallback(
    (editorInstance: editor.IStandaloneCodeEditor, monacoApi: Monaco) => {
      editorRef.current = editorInstance;
      monacoRef.current = monacoApi;
      setEditorMounted((count) => count + 1);
    },
    [],
  );

  useEffect(() => {
    const editor = editorRef.current;
    const monaco = monacoRef.current;
    if (!editor || !monaco || showDiff || !codeLoaded || !nodeStartLine) {
      return;
    }

    const isActive = phase === "playing" && highlight != null;

    const clearDecorations = () => {
      decorationIdsRef.current = editor.deltaDecorations(
        decorationIdsRef.current,
        [],
      );
    };

    const clearSync = () => {
      syncCleanupRef.current?.();
      syncCleanupRef.current = null;
    };

    if (!isActive) {
      clearDecorations();
      clearSync();
      return;
    }

    const model = editor.getModel();
    if (!model) return;

    const editorStart = absoluteToEditorLine(
      highlight.startLine,
      nodeStartLine,
    );
    const editorEnd = absoluteToEditorLine(highlight.endLine, nodeStartLine);
    const { startLine, endLine } = clampEditorRange(
      editorStart,
      editorEnd,
      model.getLineCount(),
    );

    const decorations = [];
    for (let line = 1; line <= model.getLineCount(); line += 1) {
      const inRange = line >= startLine && line <= endLine;
      decorations.push({
        range: new monaco.Range(line, 1, line, 1),
        options: {
          isWholeLine: true,
          className: inRange
            ? "walkthrough-monaco-line-deco"
            : "walkthrough-dim",
        },
      });
    }

    decorationIdsRef.current = editor.deltaDecorations(
      decorationIdsRef.current,
      decorations,
    );

    editor.revealLineInCenter(startLine);

    const domNode = editor.getDomNode();
    if (!domNode) {
      return () => {
        clearDecorations();
      };
    }

    clearSync();

    // Stable editor-level anchor: covers the whole Monaco surface and does NOT
    // move when the user scrolls code — popover stays mid-dialog on the right.
    const editorAnchor = document.createElement("div");
    editorAnchor.setAttribute("data-walkthrough-editor-anchor", "");
    editorAnchor.setAttribute("data-node-id", nodeId);
    editorAnchor.style.position = "absolute";
    editorAnchor.style.inset = "0";
    editorAnchor.style.pointerEvents = "none";
    editorAnchor.style.opacity = "0";

    const spotlight = document.createElement("div");
    spotlight.className = "walkthrough-monaco-spotlight";

    domNode.style.position = domNode.style.position || "relative";
    domNode.appendChild(editorAnchor);
    domNode.appendChild(spotlight);

    const syncSpotlight = () => {
      const layout = editor.getLayoutInfo();
      const scrollTop = editor.getScrollTop();
      const lineHeight = editor.getOption(
        monaco.editor.EditorOption.lineHeight,
      );

      const topStart = editor.getTopForLineNumber(startLine) - scrollTop;
      const topEnd = editor.getTopForLineNumber(endLine + 1) - scrollTop;

      spotlight.style.top = `${topStart}px`;
      spotlight.style.left = `${layout.contentLeft}px`;
      spotlight.style.width = `${layout.contentWidth}px`;
      spotlight.style.height = `${Math.max(lineHeight, topEnd - topStart)}px`;
    };

    syncSpotlight();
    // Bump once so the popover layer measures the editor rect after mount.
    scheduleBump();

    const scrollDisposable = editor.onDidScrollChange(syncSpotlight);
    const layoutDisposable = editor.onDidLayoutChange(() => {
      syncSpotlight();
      // Layout/size changes move the editor on screen — re-center the popover.
      scheduleBump();
    });

    syncCleanupRef.current = () => {
      scrollDisposable.dispose();
      layoutDisposable.dispose();
      spotlight.remove();
      editorAnchor.remove();
      if (bumpRafRef.current != null) {
        cancelAnimationFrame(bumpRafRef.current);
        bumpRafRef.current = null;
      }
    };

    return () => {
      clearDecorations();
      clearSync();
    };
  }, [
    phase,
    highlight,
    cursor,
    nodeStartLine,
    codeLoaded,
    showDiff,
    nodeId,
    scheduleBump,
    editorMounted,
  ]);

  return { onMount };
}
