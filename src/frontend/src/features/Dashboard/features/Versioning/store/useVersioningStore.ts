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
export interface ParentChildDiff {
  added: string[];
  removed: string[];
}

interface VersioningState {
  isOpen: boolean;
  selectedCommitId: string | null;
  nodeDiffs: Record<string, DiffStatus>;
  parentChildDiffs: Record<string, ParentChildDiff>;
  currentCommitId: string | null;
  setCurrentCommitId: (id: string | null) => void;
  setSelectedCommit: (id: string | null) => void;
  setDiffState: (
    nodeDiffs: Record<string, DiffStatus>,
    parentChildDiffs: Record<string, ParentChildDiff>
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
      currentCommitId: null,
      setCurrentCommitId: (id) => set({ currentCommitId: id }),
      togglePanel: () => set((state) => ({ isOpen: !state.isOpen })),
      setOpen: (open) => set({ isOpen: open }),
      setSelectedCommit: (id) => set({
        selectedCommitId: id,
        nodeDiffs: {},
        parentChildDiffs: {},
      }),
      setDiffState: (nodeDiffs, parentChildDiffs) => set({
        nodeDiffs,
        parentChildDiffs,
      }),
      clearDiffState: () => set({
        nodeDiffs: {},
        parentChildDiffs: {},
      }),
    }),
    { name: 'versioning-store' }
  )
);
