import { useEffect, useEffectEvent, useRef } from "react";
import type { Monaco } from "@monaco-editor/react";
import type { editor } from "monaco-editor";
import { useWalkthroughStore } from "../store/useWalkthroughStore";
import {
  absoluteToEditorLine,
  clampEditorRange,
} from "../executor/lineMapping";

interface UseWalkthroughMonacoHighlightOptions {
  editor: editor.IStandaloneCodeEditor | null;
  monaco: Monaco | null;
  nodeId: string;
  nodeStartLine?: number;
  codeLoaded: boolean;
}

export function useWalkthroughMonacoHighlight({
  editor,
  monaco,
  nodeId,
  nodeStartLine,
  codeLoaded,
}: UseWalkthroughMonacoHighlightOptions) {
  const decorationIdsRef = useRef<string[]>([]);
  const phase = useWalkthroughStore((s) => s.phase);
  const highlight = useWalkthroughStore((s) => s.highlight);
  const cursor = useWalkthroughStore((s) => s.cursor);

  const applyDecorations = useEffectEvent(() => {
    if (!editor || !monaco || !nodeStartLine || !codeLoaded) return;

    const isActive =
      phase === "playing" && highlight?.nodeId === nodeId && highlight != null;

    if (!isActive) {
      decorationIdsRef.current = editor.deltaDecorations(
        decorationIdsRef.current,
        [],
      );
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
          className: inRange ? "walkthrough-line" : "walkthrough-dim",
        },
      });
    }

    decorationIdsRef.current = editor.deltaDecorations(
      decorationIdsRef.current,
      decorations,
    );

    editor.revealLinesInCenterIfOutsideViewport(startLine, endLine);
  });

  const clearDecorations = useEffectEvent(() => {
    if (!editor) return;
    decorationIdsRef.current = editor.deltaDecorations(
      decorationIdsRef.current,
      [],
    );
  });

  useEffect(() => {
    applyDecorations();
  }, [editor, monaco, phase, highlight, cursor, nodeStartLine, codeLoaded, applyDecorations]);

  useEffect(() => {
    return () => clearDecorations();
  }, [editor, clearDecorations]);
}
