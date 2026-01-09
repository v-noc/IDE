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

type ProjectStore = SelectionSlice & FocusSlice & UISlice & DataSlice;

export const createDataSlice: StateCreator<
  ProjectStore,
  [['zustand/immer', never], ['zustand/devtools', never]],
  [],
  DataSlice
> = (set) => ({
  projectData: null,

  setProjectData: (data) => set((state) => {
    state.projectData = data;

    // Remap focus stack to new tree
    if (data && state.focusStack.length > 0) {
      const remapped = state.focusStack
        .map((n) => findNodeByKey(data, n._key))
        .filter((n): n is AnyNodeTree => n != null);
      state.focusStack = remapped;
      state.focusedNode = remapped[remapped.length - 1] ?? null;
    } else if (!data) {
      state.focusStack = [];
      state.focusedNode = null;
    }

    // Remap selected node
    if (data && state.selectedNode) {
      state.selectedNode = findNodeByKey(data, state.selectedNode._key) ?? null;
    } else if (!data) {
      state.selectedNode = null;
    }
  }),
});
