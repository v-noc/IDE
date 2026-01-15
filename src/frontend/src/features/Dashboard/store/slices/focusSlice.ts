import type { StateCreator } from 'zustand';
import type { AnyNodeTree } from '@/types/project';
import type { SelectionSlice } from './selectionSlice';
import type { UISlice } from './uiSlice';
import type { DataSlice } from './dataSlice';

export interface FocusSlice {
  focusStack: AnyNodeTree[];
  focusedNode: AnyNodeTree | null;
  focusTargetId: string | null;

  pushFocus: (node: AnyNodeTree) => void;
  popFocus: () => void;
  clearFocus: () => void;
  setFocusTargetId: (id: string | null) => void;
}

type ProjectStore = SelectionSlice & FocusSlice & UISlice & DataSlice;

export const createFocusSlice: StateCreator<
  ProjectStore,
  [['zustand/immer', never], ['zustand/devtools', never]],
  [],
  FocusSlice
> = (set) => ({
  focusStack: [],
  focusedNode: null,
  focusTargetId: null,

  pushFocus: (node) => set((state) => {
    state.focusStack.push(node);
    state.focusedNode = node;
  }),

  popFocus: () => set((state) => {
    state.focusStack.pop();
    state.focusedNode = state.focusStack[state.focusStack.length - 1] ?? null;
  }),

  clearFocus: () => set({ focusStack: [], focusedNode: null, focusTargetId: null }),

  setFocusTargetId: (id) => set({ focusTargetId: id }),
});
