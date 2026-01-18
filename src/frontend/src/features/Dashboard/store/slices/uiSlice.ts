import type { StateCreator } from 'zustand';
import type { SelectionSlice } from './selectionSlice';
import type { FocusSlice } from './focusSlice';
import type { DataSlice } from './dataSlice';

export interface UISlice {
  expandedNodeIds: Record<string, string[]>;
  activeNodeId: Record<string, string | null>;
  isDocSidebarOpen: Record<string, boolean>;
  docSidebarSize: Record<string, number>;

  toggleNodeExpansion: (tabId: string, nodeId: string) => void;
  expandNode: (tabId: string, nodeId: string) => void;
  collapseNode: (tabId: string, nodeId: string) => void;
  setActiveNodeId: (tabId: string, id: string | null) => void;
  expandNodesBulk: (tabId: string, nodeIds: string[]) => void;
  setDocSidebarOpen: (tabId: string, open: boolean) => void;
  setDocSidebarSize: (tabId: string, size: number) => void;
}

type ProjectStore = SelectionSlice & FocusSlice & UISlice & DataSlice & {
  cleanupTabData: (tabId: string) => void;
};

export const createUISlice: StateCreator<
  ProjectStore,
  [['zustand/immer', never], ['zustand/devtools', never]],
  [],
  UISlice
> = (set) => ({
  expandedNodeIds: {},
  activeNodeId: {},
  isDocSidebarOpen: {},
  docSidebarSize: {},

  toggleNodeExpansion: (tabId, nodeId) => set((state) => {
    if (!state.expandedNodeIds[tabId]) {
      state.expandedNodeIds[tabId] = [];
    }
    const index = state.expandedNodeIds[tabId].indexOf(nodeId);
    if (index > -1) {
      state.expandedNodeIds[tabId].splice(index, 1);
    } else {
      state.expandedNodeIds[tabId].push(nodeId);
    }
  }),

  expandNode: (tabId, nodeId) => set((state) => {
    if (!state.expandedNodeIds[tabId]) {
      state.expandedNodeIds[tabId] = [];
    }
    if (!state.expandedNodeIds[tabId].includes(nodeId)) {
      state.expandedNodeIds[tabId].push(nodeId);
    }
  }),

  collapseNode: (tabId, nodeId) => set((state) => {
    if (!state.expandedNodeIds[tabId]) return;
    const index = state.expandedNodeIds[tabId].indexOf(nodeId);
    if (index > -1) {
      state.expandedNodeIds[tabId].splice(index, 1);
    }
  }),

  setActiveNodeId: (tabId, id) => set((state) => {
    state.activeNodeId[tabId] = id;
  }),

  expandNodesBulk: (tabId: string, nodeIds: string[]) => set((state) => {
    if (!state.expandedNodeIds[tabId]) {
      state.expandedNodeIds[tabId] = [];
    }
    nodeIds.forEach(id => {
      if (!state.expandedNodeIds[tabId].includes(id)) {
        state.expandedNodeIds[tabId].push(id);
      }
    });
  }),

  setDocSidebarOpen: (tabId, open) => set((state) => {
    state.isDocSidebarOpen[tabId] = open;
  }),

  setDocSidebarSize: (tabId, size) => set((state) => {
    state.docSidebarSize[tabId] = size;
  }),
});
