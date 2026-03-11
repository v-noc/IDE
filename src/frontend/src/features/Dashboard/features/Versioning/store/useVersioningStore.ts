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

export type ScopeOverride = "item" | "repository";

interface VersioningState {
  isOpen: boolean;
  branch: string;
  historyScopeByTab: Record<string, HistoryScope>;
  scopeOverrideByTab: Record<string, ScopeOverride>;
  headCommitId: string | null;
  checkedOutCommitId: string | null;
  compareToCommitId: string | null;
  mergeSourceBranch: string | null;
  mergeTargetBranch: string | null;
  isMergeMode: boolean;
  diffResult: DiffResult | null;
  isLoadingDiff: boolean;
  diffError: string | null;
  activeDiffRequestId: number;
  showAffectedOnly: boolean;
  setBranch: (branch: string) => void;
  setHeadCommitId: (id: string | null) => void;
  setCheckedOutCommitId: (id: string | null) => void;
  setCompareToCommitId: (id: string | null) => void;
  setMergeSourceBranch: (name: string | null) => void;
  setMergeTargetBranch: (name: string | null) => void;
  openMergeMode: (input?: {
    sourceBranch?: string | null;
    targetBranch?: string | null;
  }) => void;
  closeMergeMode: () => void;
  loadParsedDiff: (input: {
    projectId: string;
    beforeCommitId: string;
    afterCommitId: string;
  }) => Promise<void>;
  clearComparisonState: () => void;
  togglePanel: () => void;
  setOpen: (open: boolean) => void;
  setHistoryScope: (tabId: string, scope: HistoryScope) => void;
  setScopeOverride: (tabId: string, override: ScopeOverride) => void;
  clearHistoryScope: (tabId: string) => void;
  setShowAffectedOnly: (value: boolean) => void;
  getNodeDiffStatusMap: () => Record<string, DiffType>;
  getOverlayParentChildDiffs: () => Record<string, OverlayParentChildDiff>;
}

export const useVersioningStore = create<VersioningState>()(
  devtools(
    (set, get) => ({
      isOpen: false,
      branch: "main",
      historyScopeByTab: {},
      scopeOverrideByTab: {},
      headCommitId: null,
      checkedOutCommitId: null,
      compareToCommitId: null,
      mergeSourceBranch: null,
      mergeTargetBranch: null,
      isMergeMode: false,
      diffResult: null,
      isLoadingDiff: false,
      diffError: null,
      activeDiffRequestId: 0,
      showAffectedOnly: false,
      setBranch: (branch) =>
        set((state) => (state.branch === branch ? state : { branch })),
      setHeadCommitId: (id) =>
        set((state) => (state.headCommitId === id ? state : { headCommitId: id })),
      setCheckedOutCommitId: (id) =>
        set((state) =>
          state.checkedOutCommitId === id ? state : { checkedOutCommitId: id }
        ),
      setCompareToCommitId: (id) =>
        set((state) => (state.compareToCommitId === id ? state : { compareToCommitId: id })),
      setMergeSourceBranch: (name) =>
        set((state) =>
          state.mergeSourceBranch === name ? state : { mergeSourceBranch: name }
        ),
      setMergeTargetBranch: (name) =>
        set((state) =>
          state.mergeTargetBranch === name ? state : { mergeTargetBranch: name }
        ),
      openMergeMode: (input) =>
        set((state) => ({
          isMergeMode: true,
          mergeSourceBranch: input?.sourceBranch ?? state.branch,
          mergeTargetBranch: input?.targetBranch ?? null,
          checkedOutCommitId: null,
          compareToCommitId: null,
          diffResult: null,
          isLoadingDiff: false,
          diffError: null,
          showAffectedOnly: false,
          activeDiffRequestId: state.activeDiffRequestId + 1,
        })),
      closeMergeMode: () =>
        set((state) => {
          if (
            !state.isMergeMode &&
            state.mergeSourceBranch == null &&
            state.mergeTargetBranch == null
          ) {
            return state;
          }
          return {
            isMergeMode: false,
            mergeSourceBranch: null,
            mergeTargetBranch: null,
          };
        }),
      togglePanel: () =>
        set((state) => {
          const nextOpen = !state.isOpen;
          if (nextOpen) return { isOpen: true };
          return { isOpen: false };
        }),
      setOpen: (open) =>
        set(() => ({ isOpen: open })),
      setHistoryScope: (tabId, scope) =>
        set((state) => {
          const current = state.historyScopeByTab[tabId];
          if (
            current &&
            current.scopeType === scope.scopeType &&
            current.scopeId === scope.scopeId
          ) {
            return state;
          }
          return {
            historyScopeByTab: {
              ...state.historyScopeByTab,
              [tabId]: scope,
            },
          };
        }),
      setScopeOverride: (tabId, override) =>
        set((state) => ({
          scopeOverrideByTab: {
            ...state.scopeOverrideByTab,
            [tabId]: override,
          },
        })),
      clearHistoryScope: (tabId) =>
        set((state) => {
          if (!(tabId in state.historyScopeByTab)) {
            return state;
          }
          const nextScopes = { ...state.historyScopeByTab };
          delete nextScopes[tabId];
          return { historyScopeByTab: nextScopes };
        }),
      setShowAffectedOnly: (value) =>
        set((state) => (state.showAffectedOnly === value ? state : { showAffectedOnly: value })),
      loadParsedDiff: async ({ projectId, beforeCommitId, afterCommitId }) => {
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
        set((state) => {
          if (
            state.compareToCommitId == null &&
            state.diffResult == null &&
            state.isLoadingDiff === false &&
            state.diffError == null
          ) {
            return state;
          }
          return {
            compareToCommitId: null,
            isMergeMode: false,
            mergeSourceBranch: null,
            mergeTargetBranch: null,
            diffResult: null,
            isLoadingDiff: false,
            diffError: null,
            showAffectedOnly: false,
            activeDiffRequestId: state.activeDiffRequestId + 1,
          };
        }),
      getNodeDiffStatusMap: () => buildNodeDiffStatusMap(get().diffResult),
      getOverlayParentChildDiffs: () => buildOverlayParentChildDiffs(get().diffResult),
    }),
    { name: "versioning-store" }
  )
);
