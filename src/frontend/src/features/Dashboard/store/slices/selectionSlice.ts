import type { StateCreator } from 'zustand';
import type { AnyNodeTree } from '@/types/project';
import type { FocusSlice } from './focusSlice';
import type { UISlice } from './uiSlice';
import type { DataSlice } from './dataSlice';

export interface SelectionSlice {
  selectedNode: AnyNodeTree | null;
  secondarySelectedNode: AnyNodeTree | null;
  selectedDocumentId: string | null;

  setSelectedNode: (node: AnyNodeTree | null) => void;
  setSecondarySelectedNode: (node: AnyNodeTree | null) => void;
  setSelectedDocumentId: (id: string | null) => void;
  clearSelection: () => void;
}

type ProjectStore = SelectionSlice & FocusSlice & UISlice & DataSlice;

export const createSelectionSlice: StateCreator<
  ProjectStore,
  [['zustand/immer', never], ['zustand/devtools', never]],
  [],
  SelectionSlice
> = (set) => ({
  selectedNode: null,
  secondarySelectedNode: null,
  selectedDocumentId: null,

  setSelectedNode: (node) => set({ selectedNode: node }),
  setSecondarySelectedNode: (node) => set({ secondarySelectedNode: node }),
  setSelectedDocumentId: (id) => set({ selectedDocumentId: id }),
  clearSelection: () => set({
    selectedNode: null,
    secondarySelectedNode: null,
    selectedDocumentId: null,
  }),
});
