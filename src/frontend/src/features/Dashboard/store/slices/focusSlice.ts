import type { StateCreator } from 'zustand';
import type { AnyNodeTree } from '@/types/project';
import type { SelectionSlice } from './selectionSlice';
import type { UISlice } from './uiSlice';
import type { DataSlice } from './dataSlice';
import type { TabsSlice } from './tabsSlice';

export interface FocusSlice {
  focusStack: Record<string, AnyNodeTree[]>;
  focusedNode: Record<string, AnyNodeTree | null>;
  focusTargetId: Record<string, string | null>;

  pushFocus: (tabId: string, node: AnyNodeTree) => void;
  popFocus: (tabId: string) => void;
  clearFocus: (tabId: string) => void;
  setFocusTargetId: (tabId: string, id: string | null) => void;
}

type ProjectStore = SelectionSlice & FocusSlice & UISlice & DataSlice & TabsSlice;

export const createFocusSlice: StateCreator<
  ProjectStore,
  [['zustand/immer', never], ['zustand/devtools', never]],
  [],
  FocusSlice
> = (set) => ({
  focusStack: {},
  focusedNode: {},
  focusTargetId: {},

  pushFocus: (tabId, node) => set((state) => {
    if (!state.focusStack[tabId]) {
      state.focusStack[tabId] = [];
    }
    state.focusStack[tabId].push(node);
    state.focusedNode[tabId] = node;
  }),

  popFocus: (tabId) => set((state) => {
    const stack = state.focusStack[tabId];
    if (stack && stack.length > 0) {
      stack.pop();
      state.focusedNode[tabId] = stack[stack.length - 1] ?? null;
    }
  }),

  clearFocus: (tabId) => set((state) => {
    state.focusStack[tabId] = [];
    state.focusedNode[tabId] = null;
    state.focusTargetId[tabId] = null;
  }),

  setFocusTargetId: (tabId, id) => set((state) => {
    state.focusTargetId[tabId] = id;
  }),
});
