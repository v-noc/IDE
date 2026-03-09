import { useMemo } from "react";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";

function toCodeText(value: string | object | null | undefined): string {
  if (value == null) return "";
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return "";
  }
}

function buildCodeContentCandidates(elementId: string): Set<string> {
  const candidates = new Set<string>();
  if (!elementId) return candidates;

  candidates.add(elementId);
  candidates.add(`CodeContentSchema/${elementId}`);
  candidates.add(`CodeContentSchema/${elementId.replace(/\//g, "_")}`);

  return candidates;
}

type CodePosition = {
  line_no: number;
  col_offset: number;
  end_line_no: number | null;
  end_col_offset: number | null;
};

const POSITION_FIELDS = new Set([
  "line_no",
  "col_offset",
  "end_line_no",
  "end_col_offset",
]);

function asCodePosition(value: unknown): CodePosition | null {
  if (!value || typeof value !== "object") return null;
  const v = value as Record<string, unknown>;
  if (typeof v.line_no !== "number" || typeof v.col_offset !== "number") return null;

  return {
    line_no: v.line_no,
    col_offset: v.col_offset,
    end_line_no: typeof v.end_line_no === "number" ? v.end_line_no : null,
    end_col_offset: typeof v.end_col_offset === "number" ? v.end_col_offset : null,
  };
}

function applyPositionChanges(
  base: CodePosition | null,
  changes: Array<{ field: string; oldValue: unknown; newValue: unknown }> | undefined,
  phase: "before" | "after",
): CodePosition | null {
  const relevant = (changes ?? []).filter((change) => POSITION_FIELDS.has(change.field));
  if (!base && relevant.length === 0) return null;

  const next: CodePosition = base
    ? { ...base }
    : { line_no: 1, col_offset: 0, end_line_no: null, end_col_offset: null };

  for (const change of relevant) {
    const value = phase === "before" ? change.oldValue : change.newValue;
    if (
      change.field === "line_no" ||
      change.field === "col_offset" ||
      change.field === "end_line_no" ||
      change.field === "end_col_offset"
    ) {
      if (value == null) {
        (next as Record<string, unknown>)[change.field] = null;
      } else if (typeof value === "number") {
        (next as Record<string, unknown>)[change.field] = value;
      }
    }
  }

  return next;
}

function sliceCodeByPosition(content: string, position: CodePosition | null): string {
  if (!position) return content;
  const lines = content.split(/\r?\n/);
  const startLine = Math.max(1, position.line_no);
  const endLine = position.end_line_no;
  const endCol = position.end_col_offset;
  const collected: string[] = [];

  for (let idx = 1; idx <= lines.length; idx += 1) {
    if (idx < startLine) continue;
    const line = lines[idx - 1];
    if (endLine == null || idx < endLine) {
      collected.push(line);
      continue;
    }
    if (idx === endLine) {
      collected.push(endCol == null ? line : line.slice(0, endCol));
    }
    break;
  }

  return collected.join("\n");
}

export interface UseCodeDiffResult {
  showDiff: boolean;
  originalContent: string;
  modifiedContent: string;
  isLoadingDiff: boolean;
  error: string | null;
}

interface UseCodeDiffParams {
  elementId: string;
  nodeType?: string;
  contentId?: string;
  position?: unknown;
}

export function useCodeDiff({
  elementId,
  nodeType,
  contentId,
  position,
}: UseCodeDiffParams): UseCodeDiffResult {
  const { isOpen, selectedCommitId, diffResult, isLoadingDiff, diffError } =
    useVersioningStore();

  return useMemo(() => {
    const showDiff = Boolean(isOpen && selectedCommitId);
    if (!showDiff) {
      return {
        showDiff: false,
        originalContent: "",
        modifiedContent: "",
        isLoadingDiff: false,
        error: null,
      };
    }

    if (isLoadingDiff) {
      return {
        showDiff: true,
        originalContent: "",
        modifiedContent: "",
        isLoadingDiff: true,
        error: null,
      };
    }

    if (!diffResult) {
      return {
        showDiff: true,
        originalContent: "",
        modifiedContent: "",
        isLoadingDiff: false,
        error: diffError ?? "No diff available for this selection.",
      };
    }

    const candidateIds = contentId
      ? buildCodeContentCandidates(contentId)
      : buildCodeContentCandidates(elementId);
    const contentDiff = diffResult.contentDiffs.find(
      (entry) => entry.contentType === "code" && candidateIds.has(entry.nodeId),
    );

    if (!contentDiff) {
      return {
        showDiff: true,
        originalContent: "",
        modifiedContent: "",
        isLoadingDiff: false,
        error: "No code changes for the selected node in this commit.",
      };
    }

    const beforeText = toCodeText(contentDiff.before);
    const afterText = toCodeText(contentDiff.after);

    if (nodeType === "function" || nodeType === "class") {
      const nodeDiff = diffResult.nodeDiffs.find((entry) => entry.nodeId === elementId);
      const basePosition = asCodePosition(position);
      const beforePosition = applyPositionChanges(
        basePosition,
        nodeDiff?.changes,
        "before",
      );
      const afterPosition = applyPositionChanges(basePosition, nodeDiff?.changes, "after");

      return {
        showDiff: true,
        originalContent: sliceCodeByPosition(beforeText, beforePosition),
        modifiedContent: sliceCodeByPosition(afterText, afterPosition),
        isLoadingDiff: false,
        error: null,
      };
    }

    return {
      showDiff: true,
      originalContent: beforeText,
      modifiedContent: afterText,
      isLoadingDiff: false,
      error: null,
    };
  }, [
    contentId,
    diffError,
    diffResult,
    elementId,
    isLoadingDiff,
    isOpen,
    nodeType,
    position,
    selectedCommitId,
  ]);
}
