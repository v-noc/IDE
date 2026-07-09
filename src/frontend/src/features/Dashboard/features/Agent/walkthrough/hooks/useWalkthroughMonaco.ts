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
  const anchorLine = useWalkthroughStore((s) => {
    const anchor = currentStepAnchor(s);
    return anchor?.type === "code-line" && anchor.nodeId === nodeId
      ? anchor.line
      : null;
  });
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

    const spotlight = document.createElement("div");
    spotlight.className = "walkthrough-monaco-spotlight";
    const anchorEl = document.createElement("div");
    anchorEl.setAttribute("data-walkthrough-code-anchor", "");
    anchorEl.setAttribute("data-node-id", nodeId);
    anchorEl.style.position = "absolute";
    anchorEl.style.pointerEvents = "none";
    anchorEl.style.opacity = "0";

    domNode.appendChild(spotlight);
    domNode.appendChild(anchorEl);

    const sync = () => {
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

      const absoluteAnchorLine = anchorLine ?? highlight.startLine;
      anchorEl.setAttribute("data-line", String(absoluteAnchorLine));
      const editorAnchorLine = absoluteToEditorLine(
        absoluteAnchorLine,
        nodeStartLine,
      );
      const anchorTop =
        editor.getTopForLineNumber(editorAnchorLine) - scrollTop;
      anchorEl.style.top = `${anchorTop}px`;
      anchorEl.style.left = `${layout.contentLeft}px`;
      anchorEl.style.width = `${layout.contentWidth}px`;
      anchorEl.style.height = `${lineHeight}px`;

      scheduleBump();
    };

    sync();

    const scrollDisposable = editor.onDidScrollChange(sync);
    const layoutDisposable = editor.onDidLayoutChange(sync);

    syncCleanupRef.current = () => {
      scrollDisposable.dispose();
      layoutDisposable.dispose();
      spotlight.remove();
      anchorEl.remove();
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
    anchorLine,
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
