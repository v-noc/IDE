import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

import { createSelectionSlice, type SelectionSlice } from './slices/selectionSlice';
import { createFocusSlice, type FocusSlice } from './slices/focusSlice';
import { createUISlice, type UISlice } from './slices/uiSlice';
import { createDataSlice, type DataSlice } from './slices/dataSlice';
import { createTasksSlice, type TasksSlice } from './slices/tasksSlice';

export type ProjectStore = SelectionSlice & FocusSlice & UISlice & DataSlice & TasksSlice & {
  cleanupTabData: (tabId: string) => void;
};

const useProjectStore = create<ProjectStore>()(
  devtools(
    immer((set, get, store) => ({
      ...createSelectionSlice(set, get, store),
      ...createFocusSlice(set, get, store),
      ...createUISlice(set, get, store),
      ...createDataSlice(set, get, store),
      ...createTasksSlice(set, get, store),

      cleanupTabData: (tabId: string) =>
        set((state: ProjectStore) => {
          delete state.focusStack[tabId];
          delete state.focusedNode[tabId];
          delete state.focusTargetId[tabId];
          delete state.selectedNode[tabId];
          delete state.secondarySelectedNode[tabId];
          delete state.selectedDocumentId[tabId];
          delete state.expandedNodeIds[tabId];
          delete state.activeNodeId[tabId];
          delete state.isDocSidebarOpen[tabId];
          delete state.docSidebarSize[tabId];
          delete state.lensTaskId[tabId];
          delete state.taskView[tabId];
          delete state.listCollapsed[tabId];
          delete state.listScrollToBacklog[tabId];
        }),
    })),
    { name: 'project-store' }
  )
);

export default useProjectStore;
