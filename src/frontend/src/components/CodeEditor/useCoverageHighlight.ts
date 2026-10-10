import { useCallback, useEffect, useRef, useState } from "react";
import type { Monaco } from "@monaco-editor/react";
import type { editor } from "monaco-editor";

/**
 * Highlights executed lines directly on a Monaco editor instance.
 * `startLine` is the absolute (1-based) file line that the editor's own
 * line 1 corresponds to, so covered lines (also absolute) can be mapped
 * onto the editor's own line numbers.
 */
export function useCoverageHighlight(coveredLines: number[], startLine: number) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<Monaco | null>(null);
  const decorationIdsRef = useRef<string[]>([]);
  const [editorMounted, setEditorMounted] = useState(0);
  const [showCoverage, setShowCoverage] = useState(false);

  const onMount = useCallback(
    (editorInstance: editor.IStandaloneCodeEditor, monacoApi: Monaco) => {
      editorRef.current = editorInstance;
      monacoRef.current = monacoApi;
      setEditorMounted((count) => count + 1);
    },
    [],
  );

  const hasCoverage = coveredLines.length > 0;

  useEffect(() => {
    const ed = editorRef.current;
    const monaco = monacoRef.current;
    if (!ed || !monaco) return;

    if (!showCoverage || !hasCoverage) {
      decorationIdsRef.current = ed.deltaDecorations(decorationIdsRef.current, []);
      return;
    }

    const model = ed.getModel();
    if (!model) return;
    const lineCount = model.getLineCount();
    const relativeLines = new Set(
      coveredLines
        .map((line) => line - startLine + 1)
        .filter((line) => line >= 1 && line <= lineCount),
    );

    const decorations = Array.from(relativeLines).map((line) => ({
      range: new monaco.Range(line, 1, line, 1),
      options: {
        isWholeLine: true,
        className: "coverage-line-covered",
        marginClassName: "coverage-line-covered-margin",
      },
    }));

    decorationIdsRef.current = ed.deltaDecorations(decorationIdsRef.current, decorations);
  }, [showCoverage, hasCoverage, coveredLines, startLine, editorMounted]);

  return {
    onMount,
    hasCoverage,
    showCoverage: showCoverage && hasCoverage,
    toggleCoverage: () => setShowCoverage((prev) => !prev),
  };
}
