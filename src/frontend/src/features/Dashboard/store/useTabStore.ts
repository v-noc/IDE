import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type { TabData } from '@/types/tabs';
import useProjectStore from './useProjectStore';

export interface TabState {
  tabs: Record<string, TabData>;
  rootTabId: string;
  activeTabId: string;
}

export interface TabActions {
  addTab: (tab: TabData) => void;
  removeTab: (tabId: string) => void;
  setActiveTabId: (tabId: string) => void;
  destroyTabBranch: (tabId: string) => void;
  handleNodeSelection: (tabId: string, node: any) => void;
}

export type TabStore = TabState & TabActions;

const useTabStore = create<TabStore>()(
  devtools(
    immer((set, get) => ({
      tabs: {
        root: {
          id: 'root',
          title: 'Main',
          parentId: null,
          sourceCallNodeId: null,
          childrenIds: [],
        },
      },
      rootTabId: 'root',
      activeTabId: 'root',

      addTab: (tab: TabData) =>
        set((state) => {
          console.log("addTab", tab);
          state.tabs[tab.id] = tab;
          if (tab.parentId && state.tabs[tab.parentId]) {
            state.tabs[tab.parentId].childrenIds.push(tab.id);
          }
        }),

      removeTab: (tabId: string) =>
        set((state) => {
          const tab = state.tabs[tabId];
          if (!tab) return;

          // Unlink from parent
          if (tab.parentId && state.tabs[tab.parentId]) {
            state.tabs[tab.parentId].childrenIds = state.tabs[tab.parentId].childrenIds.filter(
              (id: string) => id !== tabId
            );
          }

          // Cleanup slice data for this tab in project store
          useProjectStore.getState().cleanupTabData(tabId);

          delete state.tabs[tabId];

          // If we removed the active tab, switch back to root
          if (state.activeTabId === tabId) {
            state.activeTabId = state.rootTabId;
          }
        }),

      setActiveTabId: (tabId: string) =>
        set((state) => {
          state.activeTabId = tabId;
        }),

      destroyTabBranch: (tabId: string) => {
        const tab = get().tabs[tabId];
        if (!tab) return;

        // Destroy children first (recursive)
        tab.childrenIds.forEach((childId: string) => {
          get().destroyTabBranch(childId);
        });

        // Remove this tab (which also cleans up its slice state)
        get().removeTab(tabId);
      },

      handleNodeSelection: (tabId, node) => {

        const currentTab = get().tabs[tabId];
        if (!currentTab) return;

        // 1. Destroy existing children branch
        currentTab.childrenIds.forEach((childId) => {
          get().destroyTabBranch(childId);
        });

        // 2. Update selection for the current tab in project store
        useProjectStore.getState().setSelectedNode(tabId, node);

        // 3. If it's a CallNode, create a new child tab (Portal)
        if (node && node.node_type === 'call') {
          const callNode = node as any;
          const target = callNode.target;

          if (target) {
            const newTabId = crypto.randomUUID();
            const newTab: TabData = {
              id: newTabId,
              title: `Explore: ${target.name}`,
              parentId: tabId,
              sourceCallNodeId: node._key,
              childrenIds: [],
            };

            // Add the tab
            get().addTab(newTab);

            // Initialize the new tab's focus stack with the target in project store
            useProjectStore.getState().pushFocus(newTabId, target as any);

            // Auto-activate the new tab
            get().setActiveTabId(newTabId);
          }
        }
      },
    })),
    { name: 'tab-store' }
  )
);

export default useTabStore;
