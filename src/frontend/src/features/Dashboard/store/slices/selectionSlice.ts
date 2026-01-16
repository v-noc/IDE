import type { StateCreator } from 'zustand';
import type { AnyNodeTree } from '@/types/project';
import type { FocusSlice } from './focusSlice';
import type { UISlice } from './uiSlice';
import type { DataSlice } from './dataSlice';

export interface SelectionSlice {
  selectedNode: Record<string, AnyNodeTree | null>;
  secondarySelectedNode: Record<string, AnyNodeTree | null>;
  selectedDocumentId: Record<string, string | null>;

  setSelectedNode: (tabId: string, node: AnyNodeTree | null) => void;
  setSecondarySelectedNode: (tabId: string, node: AnyNodeTree | null) => void;
  setSelectedDocumentId: (tabId: string, id: string | null) => void;
  clearSelection: (tabId: string) => void;
}

type ProjectStore = SelectionSlice & FocusSlice & UISlice & DataSlice & {
  cleanupTabData: (tabId: string) => void;
};

export const createSelectionSlice: StateCreator<
  ProjectStore,
  [['zustand/immer', never], ['zustand/devtools', never]],
  [],
  SelectionSlice
> = (set) => ({
  selectedNode: {},
  secondarySelectedNode: {},
  selectedDocumentId: {},

  setSelectedNode: (tabId, node) => set((state) => {
    state.selectedNode[tabId] = node;
  }),
  setSecondarySelectedNode: (tabId, node) => set((state) => {
    state.secondarySelectedNode[tabId] = node;
  }),
  setSelectedDocumentId: (tabId, id) => set((state) => {
    state.selectedDocumentId[tabId] = id;
  }),
  clearSelection: (tabId) => set((state) => {
    state.selectedNode[tabId] = null;
    state.secondarySelectedNode[tabId] = null;
    state.selectedDocumentId[tabId] = null;
  }),
});
