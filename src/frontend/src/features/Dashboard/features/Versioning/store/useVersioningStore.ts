import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

/** Display format for commit items - includes derived fields from backend data */
export interface CommitDisplay {
  id: string;
  author: string;
  initials: string;
  timestamp: string;
  message: string;
}

export type DiffStatus = 'added' | 'removed' | 'updated' | null;
export interface DiffNodeRef {
  id: string;
  body?: Record<string, unknown>;
}
export interface ParentChildDiff {
  added: DiffNodeRef[];
  removed: DiffNodeRef[];
}

interface VersioningState {
  isOpen: boolean;
  selectedCommitId: string | null;
  nodeDiffs: Record<string, DiffStatus>;
  parentChildDiffs: Record<string, ParentChildDiff>;
  diffNodesMap: Record<string, Record<string, unknown>>;
  currentCommitId: string | null;
  setCurrentCommitId: (id: string | null) => void;
  setSelectedCommit: (id: string | null) => void;
  setDiffState: (
    nodeDiffs: Record<string, DiffStatus>,
    parentChildDiffs: Record<string, ParentChildDiff>,
    diffNodesMap: Record<string, Record<string, unknown>>
  ) => void;
  clearDiffState: () => void;
  togglePanel: () => void;
  setOpen: (open: boolean) => void;
}

export const useVersioningStore = create<VersioningState>()(
  devtools(
    (set) => ({
      isOpen: false,
      selectedCommitId: null,
      nodeDiffs: {},
      parentChildDiffs: {},
      diffNodesMap: {},
      currentCommitId: null,
      setCurrentCommitId: (id) => set({ currentCommitId: id }),
      togglePanel: () => set((state) => ({ isOpen: !state.isOpen })),
      setOpen: (open) => set({ isOpen: open }),
      setSelectedCommit: (id) => set({
        selectedCommitId: id,
        nodeDiffs: {},
        parentChildDiffs: {},
        diffNodesMap: {},
      }),
      setDiffState: (nodeDiffs, parentChildDiffs, diffNodesMap) => set({
        nodeDiffs,
        parentChildDiffs,
        diffNodesMap,
      }),
      clearDiffState: () => set({
        nodeDiffs: {},
        parentChildDiffs: {},
        diffNodesMap: {},
      }),
    }),
    { name: 'versioning-store' }
  )
);
