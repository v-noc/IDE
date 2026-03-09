import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { versioningDiffService } from "../services/versioningDiffService";
import type { DiffResult, DiffType, NodeDiff } from "../types/diff";

export interface CommitDisplay {
  id: string;
  author: string;
  initials: string;
  timestamp: string;
  message: string;
}

export interface OverlayDiffNodeRef {
  id: string;
  body?: Record<string, unknown>;
}

export interface OverlayParentChildDiff {
  added: OverlayDiffNodeRef[];
  removed: OverlayDiffNodeRef[];
}

export interface HistoryScope {
  scopeType: string;
  scopeId: string | null;
}

function nodeBodyForOverlay(nodeDiff: NodeDiff | undefined): Record<string, unknown> | undefined {
  if (!nodeDiff) return undefined;
  return nodeDiff.after ?? nodeDiff.before;
}

function buildNodeDiffStatusMap(diffResult: DiffResult | null): Record<string, DiffType> {
  if (!diffResult) return {};
  return diffResult.nodeDiffs.reduce<Record<string, DiffType>>((acc, node) => {
    acc[node.nodeId] = node.status;
    return acc;
  }, {});
}

function buildOverlayParentChildDiffs(
  diffResult: DiffResult | null
): Record<string, OverlayParentChildDiff> {
  if (!diffResult) return {};
  const nodeDiffMap = new Map(diffResult.nodeDiffs.map((node) => [node.nodeId, node]));
  const result: Record<string, OverlayParentChildDiff> = {};

  for (const item of diffResult.relationshipChanges.added) {
    const current = result[item.parent] ?? { added: [], removed: [] };
    const body = nodeBodyForOverlay(nodeDiffMap.get(item.child));
    current.added.push({ id: item.child, ...(body ? { body } : {}) });
    result[item.parent] = current;
  }
  for (const item of diffResult.relationshipChanges.removed) {
    const current = result[item.parent] ?? { added: [], removed: [] };
    const body = nodeBodyForOverlay(nodeDiffMap.get(item.child));
    current.removed.push({ id: item.child, ...(body ? { body } : {}) });
    result[item.parent] = current;
  }

  return result;
}

interface VersioningState {
  isOpen: boolean;
  historyScopeByTab: Record<string, HistoryScope>;
  selectedCommitId: string | null;
  currentCommitId: string | null;
  diffResult: DiffResult | null;
  isLoadingDiff: boolean;
  diffError: string | null;
  activeDiffRequestId: number;
  setCurrentCommitId: (id: string | null) => void;
  setSelectedCommit: (id: string | null) => void;
  loadParsedDiff: (input: {
    projectId: string;
    beforeCommitId: string;
    afterCommitId: string;
  }) => Promise<void>;
  clearComparisonState: () => void;
  togglePanel: () => void;
  setOpen: (open: boolean) => void;
  setHistoryScope: (tabId: string, scope: HistoryScope) => void;
  clearHistoryScope: (tabId: string) => void;
  getNodeDiffStatusMap: () => Record<string, DiffType>;
  getOverlayParentChildDiffs: () => Record<string, OverlayParentChildDiff>;
}

export const useVersioningStore = create<VersioningState>()(
  devtools(
    (set, get) => ({
      isOpen: false,
      historyScopeByTab: {},
      selectedCommitId: null,
      currentCommitId: null,
      diffResult: null,
      isLoadingDiff: false,
      diffError: null,
      activeDiffRequestId: 0,
      setCurrentCommitId: (id) => set({ currentCommitId: id }),
      togglePanel: () =>
        set((state) => {
          const nextOpen = !state.isOpen;
          if (nextOpen) return { isOpen: true };
          return {
            isOpen: false,
            selectedCommitId: null,
            diffResult: null,
            isLoadingDiff: false,
            diffError: null,
            activeDiffRequestId: state.activeDiffRequestId + 1,
          };
        }),
      setOpen: (open) =>
        set((state) => {
          if (open) return { isOpen: true };
          return {
            isOpen: false,
            selectedCommitId: null,
            diffResult: null,
            isLoadingDiff: false,
            diffError: null,
            activeDiffRequestId: state.activeDiffRequestId + 1,
          };
        }),
      setHistoryScope: (tabId, scope) =>
        set((state) => ({
          historyScopeByTab: {
            ...state.historyScopeByTab,
            [tabId]: scope,
          },
        })),
      clearHistoryScope: (tabId) =>
        set((state) => {
          if (!(tabId in state.historyScopeByTab)) {
            return {};
          }
          const nextScopes = { ...state.historyScopeByTab };
          delete nextScopes[tabId];
          return { historyScopeByTab: nextScopes };
        }),
      setSelectedCommit: (id) => set({ selectedCommitId: id }),
      loadParsedDiff: async ({ projectId, beforeCommitId, afterCommitId }) => {
        if (!get().isOpen) {
          return;
        }
        if (!projectId || !beforeCommitId || !afterCommitId || beforeCommitId === afterCommitId) {
          set({ diffResult: null, isLoadingDiff: false, diffError: null });
          return;
        }

        const requestId = get().activeDiffRequestId + 1;
        set({
          isLoadingDiff: true,
          diffError: null,
          activeDiffRequestId: requestId,
        });

        try {
          const parsed = await versioningDiffService.fetchParsedDiff({
            projectId,
            beforeCommitId,
            afterCommitId,
          });
          if (get().activeDiffRequestId !== requestId) return;
          set({ diffResult: parsed, isLoadingDiff: false, diffError: null });
        } catch (error) {
          if (get().activeDiffRequestId !== requestId) return;
          set({
            isLoadingDiff: false,
            diffResult: null,
            diffError:
              error instanceof Error
                ? error.message
                : "Failed to fetch and parse diff payload",
          });
        }
      },
      clearComparisonState: () =>
        set((state) => ({
          selectedCommitId: null,
          diffResult: null,
          isLoadingDiff: false,
          diffError: null,
          activeDiffRequestId: state.activeDiffRequestId + 1,
        })),
      getNodeDiffStatusMap: () => buildNodeDiffStatusMap(get().diffResult),
      getOverlayParentChildDiffs: () => buildOverlayParentChildDiffs(get().diffResult),
    }),
    { name: "versioning-store" }
  )
);
