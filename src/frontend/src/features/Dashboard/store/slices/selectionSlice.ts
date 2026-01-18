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
    const previousNode = state.selectedNode[tabId];
    state.selectedNode[tabId] = node;
    state.secondarySelectedNode[tabId] = null;
    
    // Clear document selection when node changes (will be synced by useWorkspaceDocs)
    if (previousNode?._key !== node?._key) {
      state.selectedDocumentId[tabId] = null;
    }
  }),
  setSecondarySelectedNode: (tabId, node) => set((state) => {
    const previousSecondaryNode = state.secondarySelectedNode[tabId];
    state.secondarySelectedNode[tabId] = node;
    
    // Clear document selection when secondary node changes (will be synced by useWorkspaceDocs)
    if (previousSecondaryNode?._key !== node?._key) {
      state.selectedDocumentId[tabId] = null;
    }
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
