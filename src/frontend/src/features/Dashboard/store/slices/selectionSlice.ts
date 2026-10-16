import type { StateCreator } from 'zustand';
import type { AnyNodeTree } from '@/types/project';
import type { FocusSlice } from './focusSlice';
import type { UISlice } from './uiSlice';
import type { DataSlice } from './dataSlice';

export interface SelectionSlice {
  selectedNode: Record<string, AnyNodeTree | null>;
  secondarySelectedNode: Record<string, AnyNodeTree | null>;
  // Purely a visual "point at this node on canvas" pointer (e.g. revealing a log
  // row's underlying node). Unlike secondarySelectedNode, nothing uses this to
  // decide what content (logs/code/docs/playground) to show - setting it must
  // never change which node those panels are scoped to.
  highlightedNode: Record<string, AnyNodeTree | null>;
  selectedDocumentId: Record<string, string | null>;

  setSelectedNode: (tabId: string, node: AnyNodeTree | null) => void;
  setSecondarySelectedNode: (tabId: string, node: AnyNodeTree | null) => void;
  setHighlightedNode: (tabId: string, node: AnyNodeTree | null) => void;
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
  highlightedNode: {},
  selectedDocumentId: {},

  setSelectedNode: (tabId, node) => set((state) => {
    const previousNode = state.selectedNode[tabId];
    state.selectedNode[tabId] = node;
    state.secondarySelectedNode[tabId] = null;
    state.highlightedNode[tabId] = null;

    // Clear document selection when node changes (will be synced by useWorkspaceDocs)
    if (previousNode?.id !== node?.id) {
      state.selectedDocumentId[tabId] = null;
    }
  }),
  setSecondarySelectedNode: (tabId, node) => set((state) => {
    const previousSecondaryNode = state.secondarySelectedNode[tabId];
    state.secondarySelectedNode[tabId] = node;
    state.highlightedNode[tabId] = null;

    // Clear document selection when secondary node changes (will be synced by useWorkspaceDocs)
    if (previousSecondaryNode?.id !== node?.id) {
      state.selectedDocumentId[tabId] = null;
    }
  }),
  setHighlightedNode: (tabId, node) => set((state) => {
    state.highlightedNode[tabId] = node;
  }),
  setSelectedDocumentId: (tabId, id) => set((state) => {
    state.selectedDocumentId[tabId] = id;
  }),
  clearSelection: (tabId) => set((state) => {
    state.selectedNode[tabId] = null;
    state.secondarySelectedNode[tabId] = null;
    state.highlightedNode[tabId] = null;
    state.selectedDocumentId[tabId] = null;
  }),
});
