import type { StateCreator } from 'zustand';
import type { AnyNodeTree, ProjectNodeTree } from '@/types/project';
import { findNodeByKey } from '@/features/Dashboard/utils/findNode';
import type { SelectionSlice } from './selectionSlice';
import type { FocusSlice } from './focusSlice';
import type { UISlice } from './uiSlice';

export interface DataSlice {
  projectData: ProjectNodeTree | null;
  setProjectData: (data: ProjectNodeTree | null) => void;
}

type ProjectStore = SelectionSlice & FocusSlice & UISlice & DataSlice & {
  cleanupTabData: (tabId: string) => void;
};

export const createDataSlice: StateCreator<
  ProjectStore,
  [['zustand/immer', never], ['zustand/devtools', never]],
  [],
  DataSlice
> = (set) => ({
  projectData: null,

  setProjectData: (data) => set((state) => {
    state.projectData = data;

    if (data) {
      // Remap focus stack for each tab
      Object.keys(state.focusStack).forEach((tabId) => {
        const stack = state.focusStack[tabId];
        if (stack && stack.length > 0) {
          const remapped = stack
            .map((n) => findNodeByKey(data, n._key))
            .filter((n): n is AnyNodeTree => n != null);
          state.focusStack[tabId] = remapped;
          state.focusedNode[tabId] = remapped[remapped.length - 1] ?? null;
        }
      });

      // Remap selected node for each tab
      Object.keys(state.selectedNode).forEach((tabId) => {
        const selected = state.selectedNode[tabId];
        if (selected) {
          state.selectedNode[tabId] = findNodeByKey(data, selected._key) ?? null;
        }
      });
    } else {
      // Clear all tabs if no data
      state.focusStack = {};
      state.focusedNode = {};
      state.selectedNode = {};
      state.secondarySelectedNode = {};
      state.selectedDocumentId = {};
      state.expandedNodeIds = {};
      state.activeNodeId = {};
      state.focusTargetId = {};
    }
  }),
});
