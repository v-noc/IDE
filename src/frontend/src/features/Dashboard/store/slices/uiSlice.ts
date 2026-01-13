import type { StateCreator } from 'zustand';
import type { SelectionSlice } from './selectionSlice';
import type { FocusSlice } from './focusSlice';
import type { DataSlice } from './dataSlice';

export interface UISlice {
  expandedNodeIds: string[];
  activeNodeId: string | null;

  toggleNodeExpansion: (nodeId: string) => void;
  expandNode: (nodeId: string) => void;
  collapseNode: (nodeId: string) => void;
  setActiveNodeId: (id: string | null) => void;
}

type ProjectStore = SelectionSlice & FocusSlice & UISlice & DataSlice;

export const createUISlice: StateCreator<
  ProjectStore,
  [['zustand/immer', never], ['zustand/devtools', never]],
  [],
  UISlice
> = (set) => ({
  expandedNodeIds: [],
  activeNodeId: null,

  toggleNodeExpansion: (nodeId) => set((state) => {
    const index = state.expandedNodeIds.indexOf(nodeId);
    if (index > -1) {
      state.expandedNodeIds.splice(index, 1);
    } else {
      state.expandedNodeIds.push(nodeId);
    }
  }),

  expandNode: (nodeId) => set((state) => {
    if (!state.expandedNodeIds.includes(nodeId)) {
      state.expandedNodeIds.push(nodeId);
    }
  }),

  collapseNode: (nodeId) => set((state) => {
    const index = state.expandedNodeIds.indexOf(nodeId);
    if (index > -1) {
      state.expandedNodeIds.splice(index, 1);
    }
  }),

  setActiveNodeId: (id) => set({ activeNodeId: id }),
});
